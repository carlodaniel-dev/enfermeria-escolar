
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine

router = APIRouter(
    prefix="/catalogos",
    tags=["Catálogos"],
)


@router.get("")
def obtener_catalogos():
    consultas = {
        "cursos": """
            SELECT id, nombre, nivel
            FROM public.curso
            ORDER BY id
        """,
        "paralelos": """
            SELECT id, nombre
            FROM public.paralelo
            ORDER BY id
        """,
        "especialidades": """
            SELECT id, nombre
            FROM public.especialidad
            ORDER BY id
        """,
        "diagnosticos": """
            SELECT id, nombre
            FROM public.diagnostico
            WHERE activo = TRUE
            ORDER BY id
        """,
    }

    try:
        with engine.connect() as connection:
            resultado = {}

            for nombre, consulta in consultas.items():
                filas = connection.execute(
                    text(consulta)
                ).mappings().all()

                resultado[nombre] = [
                    dict(fila) for fila in filas
                ]

            return resultado

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar los catálogos.",
        )
