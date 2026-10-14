
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

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
def listar_estudiantes():
    try:
        return obtener_estudiantes()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar los estudiantes.",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
def registrar_estudiante(datos: EstudianteCrear):
    try:
        return crear_estudiante(datos)

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail=(
                "No se pudo registrar el estudiante. "
                "Verifica los datos relacionados."
            ),
        ) from error

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible guardar el estudiante.",
        ) from error
