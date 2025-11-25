# api/index.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse, Response
from pydantic import BaseModel, Field
from typing import List, Optional
from docxtpl import DocxTemplate
import json
import io
import os

app = FastAPI(title="Catastro → DOCX", version="1.0")

# === CORS Manual (Método más confiable en Vercel) ===
ALLOWED_ORIGINS = [
    "https://gf7ef8efb74e614-h00tgkrff41zo9rl.adb.us-phoenix-1.oraclecloudapps.com",
    "https://gf7ef8efb74e614-ys0k48631ld4v415.adb.us-phoenix-1.oraclecloudapps.com",
    "https://censoedomex.maxapex.net",
    "http://localhost:3000",
]

def get_cors_headers(origin: str = None):
    """Genera headers CORS dinámicamente"""
    # Si el origin está en la lista permitida, úsalo; si no, usa el primero
    allowed_origin = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    
    return {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Expose-Headers": "Content-Disposition",
        "Access-Control-Max-Age": "3600",
    }

@app.middleware("http")
async def add_cors_middleware(request: Request, call_next):
    """Middleware para agregar CORS a TODAS las respuestas"""
    origin = request.headers.get("origin", "")
    
    # Manejar preflight OPTIONS
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers=get_cors_headers(origin)
        )
    
    # Procesar request normal
    response = await call_next(request)
    
    # Agregar headers CORS a la respuesta
    cors_headers = get_cors_headers(origin)
    for key, value in cors_headers.items():
        response.headers[key] = value
    
    return response

# === Modelos Pydantic ===
class Terreno(BaseModel):
    valor_terreno_propio: int = Field(..., ge=0)
    metros_terreno_propio: Optional[float] = None
    valor_terreno_comun: int = Field(..., ge=0)
    metros_terreno_comun: int = Field(..., ge=0)

class Construccion(BaseModel):
    valor_construccion_propia: int = Field(..., ge=0)
    metros_construccion_propia: int = Field(..., ge=0)
    valor_construccion_comun: int = Field(..., ge=0)
    metros_construccion_comun: int = Field(..., ge=0)

class Impuesto(BaseModel):
    recargo: Optional[float] = None
    multa: Optional[float] = None
    gastos: Optional[float] = None
    subsidios: Optional[float] = None
    suma: Optional[float] = None
    ultimo_periodo_pagado: Optional[str] = None
    impuesto_predial: Optional[float] = None
    cantidad_con_letra: Optional[str] = None

class Predio(BaseModel):
    clave_catastral: str = Field(..., pattern=r"^\d{3}-\d{2}-\d{3}-\d{2}-\d{2}-[A-Z0-9]+$")
    folio: int = Field(..., gt=0)
    direccion: str
    contribuyente: str
    terreno: Terreno
    construccion: Construccion
    impuesto: Impuesto

class DocumentoCatastral(BaseModel):
    archivo: str
    predio: List[Predio]

# === Endpoints ===
@app.get("/")
@app.get("/api")
async def root():
    return {
        "message": "API FastAPI en Vercel + APEX funcionando 🚀",
        "status": "ok",
        "cors": "enabled",
        "allowed_origins": ALLOWED_ORIGINS
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "cors": "enabled",
        "endpoints": ["/api/generar-docx"],
        "allowed_origins": ALLOWED_ORIGINS
    }

@app.post("/api/generar-docx")
async def generar_docx(file: UploadFile = File(...)):
    """Genera un documento DOCX a partir de un JSON validado"""
    
    # Validar extensión
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "Solo se permiten archivos .json")
    
    # Leer y validar JSON
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        doc_data = DocumentoCatastral.model_validate(data)
    except json.JSONDecodeError as e:
        raise HTTPException(422, f"JSON inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(422, f"Error de validación: {str(e)}")
    
    # Cargar plantilla
    template_path = "1785-003.docx"
    if not os.path.exists(template_path):
        raise HTTPException(500, f"Plantilla {template_path} no encontrada")
    
    try:
        doc = DocxTemplate(template_path)
        doc.render(doc_data.model_dump())
        
        # Generar archivo en memoria
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        # Nombre del archivo
        nombre_archivo = doc_data.archivo
        if not nombre_archivo.endswith(".docx"):
            nombre_archivo = f"{nombre_archivo}.docx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
            }
        )
    except Exception as e:
        raise HTTPException(500, f"Error generando documento: {str(e)}")

# Endpoint de prueba simple
@app.get("/api/test-cors")
async def test_cors():
    return {"message": "Si ves esto, CORS está funcionando correctamente"}
