
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.dependencies import obtener_usuario_actual
from app.schemas.estudiante import EstudianteCrear
from app.services.estudiante_service import (
    crear_estudiante,
    obtener_estudiantes,
)

router = APIRouter(
    prefix="/estudiantes",
    tags=["Estudiantes"],
)


@router.get("")
def listar_estudiantes(
    usuario: dict = Depends(obtener_usuario_actual),
):
    try:
        return obtener_estudiantes()

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible consultar los estudiantes.",
        ) from error


@router.post("", status_code=status.HTTP_201_CREATED)
def registrar_estudiante(
    datos: EstudianteCrear,
    usuario: dict = Depends(obtener_usuario_actual),
):
    try:
        return crear_estudiante(datos)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se pudo registrar el estudiante. "
                "Verifica los datos relacionados."
            ),
        ) from error

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible guardar el estudiante.",
        ) from error
