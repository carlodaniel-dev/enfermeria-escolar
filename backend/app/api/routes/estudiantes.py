
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.dependencies import exigir_admin, obtener_usuario_actual
from app.schemas.estudiante import EstudianteActualizar, EstudianteCrear

from app.services.estudiante_service import (
    actualizar_estudiante,
    crear_estudiante,
    obtener_auditoria_estudiante,
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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


@router.put("/{estudiante_id}")
def modificar_estudiante(
    estudiante_id: int,
    datos: EstudianteActualizar,
    usuario: dict = Depends(obtener_usuario_actual),
):
    if estudiante_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El ID del estudiante debe ser positivo.",
        )

    try:
        return actualizar_estudiante(
            estudiante_id=estudiante_id,
            datos=datos,
            usuario_id=usuario["id"],
        )
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
            detail="No se pudo modificar el estudiante. Verifica los datos relacionados.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible modificar el estudiante.",
        ) from error


@router.get("/{estudiante_id}/auditoria")
def consultar_auditoria_estudiante(
    estudiante_id: int,
    usuario: dict = Depends(exigir_admin),
):
    if estudiante_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El ID del estudiante debe ser positivo.",
        )

    try:
        return obtener_auditoria_estudiante(estudiante_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible consultar la auditoría del estudiante.",
        ) from error
