
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.schemas.atencion import AtencionCrear
from app.services.atencion_service import crear_atencion
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
    usuario_id: int = Query(gt=0),
):
    try:
        return crear_atencion(datos, usuario_id)

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Los datos no cumplen las restricciones de la base de datos.",
        ) from error

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible registrar la atención.",
        ) from error


@router.get("")
def listar_atenciones():
    try:
        return obtener_atenciones()

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar las atenciones.",
        ) from error
