
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.dependencies import obtener_usuario_actual
from app.schemas.atencion import (
    AtencionActualizar,
    AtencionCrear,
    AtencionRespuesta,
)
from app.services.atencion_service import (
    actualizar_atencion,
    crear_atencion,
    obtener_atenciones,
)

router = APIRouter(prefix="/atenciones", tags=["Atenciones"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AtencionRespuesta,
)
def registrar_atencion(
    datos: AtencionCrear,
    usuario: dict = Depends(obtener_usuario_actual),
):
    try:
        return crear_atencion(datos, usuario["id"])

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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


@router.put(
    "/{atencion_id}",
    response_model=AtencionRespuesta,
)
def modificar_atencion(
    atencion_id: int = Path(
        gt=0,
        description="Identificador positivo de la atención.",
    ),
    datos: AtencionActualizar = ...,
    usuario: dict = Depends(obtener_usuario_actual),
):
    try:
        return actualizar_atencion(
            atencion_id=atencion_id,
            datos=datos,
            usuario_actual=usuario,
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
            detail="No fue posible modificar la atención.",
        ) from error
