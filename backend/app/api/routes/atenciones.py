
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.dependencies import obtener_usuario_actual
from app.schemas.atencion import AtencionCrear
from app.services.atencion_service import (
    crear_atencion,
    obtener_atenciones,
)

router = APIRouter(
    prefix="/atenciones",
    tags=["Atenciones"],
)


@router.post("", status_code=status.HTTP_201_CREATED)
def registrar_atencion(
    datos: AtencionCrear,
    usuario: dict = Depends(obtener_usuario_actual),
):
    try:
        return crear_atencion(datos, usuario["id"])

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Los datos no cumplen las restricciones de la base de datos.",
        ) from error

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible registrar la atención.",
        ) from error


@router.get("")
def listar_atenciones(
    usuario: dict = Depends(obtener_usuario_actual),
):
    try:
        return obtener_atenciones()

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible consultar las atenciones.",
        ) from error
