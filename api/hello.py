from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
import os

app = FastAPI()

# Esto evita TODOS los problemas de CORS en Vercel + APEX
@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "https://censoedomex.maxapex.net"  # ← tu APEX
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Responde al preflight OPTIONS (OBLIGATORIO)
@app.options("/{full_path:path}")
async def preflight():
    return JSONResponse(status_code=200)

# Tu endpoint real (PDF, DOCX, JSON, lo que quieras)
@app.post("/generar-docx")
@app.get("/generar-docx")  # opcional, para pruebas
async def generar_docx():
    # Ejemplo: devolver un PDF de prueba
    # Reemplaza esto con tu lógica real (python-docx, Gotenberg, etc.)
    pdf_path = "sample.pdf"  # pon aquí tu archivo generado
    
    if not os.path.exists(pdf_path):
        return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="Datos históricos por sitio.pdf"
    )

# Ruta de prueba rápida
@app.get("/")
async def root():
    return {"message": "¡API en Vercel funcionando perfecto! 🚀"}
