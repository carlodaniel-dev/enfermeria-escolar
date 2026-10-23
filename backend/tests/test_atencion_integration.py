
import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings
from app.db.session import engine


BASE_DATOS_PRUEBAS = "enfermeria_escolar"


def verificar_base_de_datos():
    assert settings.DB_NAME == BASE_DATOS_PRUEBAS

    with engine.connect() as connection:
        base_actual = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    assert base_actual == BASE_DATOS_PRUEBAS


def ejecutar_insert_atencion(
    diagnostico_id: int,
    descripcion_diagnostico: str | None,
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO public.atencion (
                    estudiante_id,
                    fecha_hora,
                    diagnostico_id,
                    descripcion_diagnostico,
                    usuario_id
                )
                VALUES (
                    :estudiante_id,
                    CURRENT_TIMESTAMP,
                    :diagnostico_id,
                    :descripcion_diagnostico,
                    :usuario_id
                )
            """),
            {
                "estudiante_id": 1,
                "diagnostico_id": diagnostico_id,
                "descripcion_diagnostico": descripcion_diagnostico,
                "usuario_id": 1,
            },
        )


def test_trigger_rechaza_otros_sin_descripcion():
    verificar_base_de_datos()

    with pytest.raises(
        ProgrammingError,
        match=r"Debe ingresar una descripción cuando el diagnóstico es Otros",
    ):
        ejecutar_insert_atencion(
            diagnostico_id=10,
            descripcion_diagnostico=None,
        )


def test_trigger_rechaza_descripcion_en_diagnostico_normal():
    verificar_base_de_datos()

    with pytest.raises(
        ProgrammingError,
        match=r"La descripción adicional solo se permite para el diagnóstico Otros",
    ):
        ejecutar_insert_atencion(
            diagnostico_id=1,
            descripcion_diagnostico="Descripción no permitida",
        )


def test_trigger_rechaza_cambiar_fecha_original():
    verificar_base_de_datos()

    with engine.begin() as connection:
        with pytest.raises(
            ProgrammingError,
            match=r"No se puede cambiar la fecha original de la atención",
        ):
            connection.execute(
                text("""
                    UPDATE public.atencion
                    SET fecha_hora = fecha_hora + INTERVAL '1 day'
                    WHERE id = (
                        SELECT MIN(id)
                        FROM public.atencion
                    )
                """)
            )


def test_trigger_rechaza_cambiar_usuario_original():
    verificar_base_de_datos()

    with engine.begin() as connection:
        with pytest.raises(
            ProgrammingError,
            match=r"No se puede cambiar el usuario que registró la atención",
        ):
            connection.execute(
                text("""
                    UPDATE public.atencion
                    SET usuario_id = CASE
                        WHEN usuario_id = 1 THEN 2
                        ELSE 1
                    END
                    WHERE id = (
                        SELECT MIN(id)
                        FROM public.atencion
                    )
                """)
            )


def test_trigger_actualiza_fecha_modificacion():
    verificar_base_de_datos()

    with engine.connect() as connection:
        transaccion = connection.begin()

        try:
            atencion = connection.execute(
                text("""
                    SELECT id, fecha_modificacion
                    FROM public.atencion
                    ORDER BY id
                    LIMIT 1
                """)
            ).mappings().one()

            fecha_anterior = atencion["fecha_modificacion"]

            connection.execute(
                text("""
                    UPDATE public.atencion
                    SET recomendacion = COALESCE(recomendacion, '')
                        || ' TEST_AUDITORIA'
                    WHERE id = :id
                """),
                {"id": atencion["id"]},
            )

            fecha_nueva = connection.execute(
                text("""
                    SELECT fecha_modificacion
                    FROM public.atencion
                    WHERE id = :id
                """),
                {"id": atencion["id"]},
            ).scalar_one()

            assert fecha_nueva is not None

            if fecha_anterior is not None:
                assert fecha_nueva >= fecha_anterior

        finally:
            transaccion.rollback()
