
from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="Sistema de Enfermería Escolar",
    description=(
        "API para la gestión de estudiantes "
        "y atenciones de enfermería escolar."
    ),
    version="0.1.0",
)

app.include_router(api_router, prefix="/api")


@app.get("/", tags=["General"])
def root():
    return {
        "mensaje": "API de Enfermería Escolar",
        "estado": "en funcionamiento",
        "version": "0.1.0",
    }


@app.get("/health", tags=["General"])
def health_check():
    return {
        "estado": "ok",
        "servicio": "backend",
    }
