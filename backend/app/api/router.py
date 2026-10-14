
from fastapi import APIRouter

from app.api.routes import auth, catalogos, estudiantes, atenciones

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(catalogos.router)
api_router.include_router(estudiantes.router)
api_router.include_router(atenciones.router)
