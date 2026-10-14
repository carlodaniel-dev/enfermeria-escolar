
from fastapi import APIRouter

from app.api.routes import catalogos, estudiantes, atenciones

api_router = APIRouter()

api_router.include_router(catalogos.router)
api_router.include_router(estudiantes.router)
api_router.include_router(atenciones.router)
