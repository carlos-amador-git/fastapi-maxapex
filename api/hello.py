# api/index.py   ← este debe ser el nombre exacto del archivo

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

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
    #response.headers["Access-Control-Allow-Origin"] = "https://gf7ef8efb74e614-ys0k48631ld4v415.adb.us-phoenix-1.oraclecloudapps.com"
    response.headers["Access-Control-Allow-Origin"] = "https://censoedomex.maxapex.net"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Tu endpoint real (ahora con la ruta correcta)
@app.get("/api/generar-docx")
@app.post("/api/generar-docx")
async def generar_docx():
    pdf_path = "sample.pdf"  # ← cambia por tu lógica real de generación

    if not os.path.exists(pdf_path):
        return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="Datos históricos por sitio.pdf"
    )

# Ruta de prueba
@app.get("/")
@app.get("/api")
async def root():
    return {"message": "API FastAPI en Vercel + APEX funcionando al 100% 🚀"}
