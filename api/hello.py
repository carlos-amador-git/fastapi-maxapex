# api/index.py   ← este debe ser el nombre exacto del archivo

##from fastapi import FastAPI, Request
##from fastapi.responses import JSONResponse, FileResponse
##from fastapi.middleware.cors import CORSMiddleware
##import os

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from docxtpl import DocxTemplate
import json
import io
import os

##app = FastAPI()
app = FastAPI(title="Catastro → DOCX", version="1.0")

# CORS amplio (puedes restringirlo después)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Esto es lo IMPORTANTE: capturar OPTIONS en TODAS las rutas incluyendo /api/*
@app.options("/api/{full_path:path}")
@app.options("/{full_path:path}")
async def preflight_handler():
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Middleware para forzar headers en todas las respuestas (por si acaso)
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "https://gf7ef8efb74e614-ys0k48631ld4v415.adb.us-phoenix-1.oraclecloudapps.com"
    #response.headers["Access-Control-Allow-Origin"] = "https://censoedomex.maxapex.net"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# === Tus modelos Pydantic (sin cambios) ===
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
    
# Tu endpoint real (ahora con la ruta correcta)
@app.get("/api/generar-docx")
@app.post("/api/generar-docx")
async def generar_docx(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "Solo se permiten archivos .json")

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        doc_data = DocumentoCatastral.model_validate(data)
    except Exception as e:
        raise HTTPException(422, f"Error en JSON o validación: {str(e)}")

    template_path = "1785-003.docx"
    if not os.path.exists(template_path):
        raise HTTPException(500, "Plantilla template.docx no encontrada")

    doc = DocxTemplate(template_path)
    doc.render(doc_data.model_dump())

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)

    # Usar el nombre que viene en el JSON
    nombre_archivo = doc_data.archivo if doc_data.archivo.endswith(".docx") else f"{doc_data.archivo}.docx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{nombre_archivo}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
    )
##async def generar_docx():
  ##  pdf_path = "sample.pdf"  # ← cambia por tu lógica real de generación

    ##if not os.path.exists(pdf_path):
      ##  return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)

    ##return FileResponse(
      ##  pdf_path,
       ## media_type="application/pdf",
        ##filename="Datos históricos por sitio.pdf"
    ##)

# Ruta de prueba
@app.get("/")
@app.get("/api")
async def root():
    return {"message": "API FastAPI en Vercel + APEX funcionando al 100% 🚀"}
