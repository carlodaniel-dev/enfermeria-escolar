
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings
from app.db.session import engine
from app.schemas.estudiante import EstudianteActualizar, EstudianteCrear
from app.services import estudiante_service


BASE_DATOS_PRUEBAS = "enfermeria_escolar"


@pytest.fixture
def estudiante_temporal():
    # Verificación adicional: nunca ejecutar contra la base de desarrollo.
    if settings.DB_NAME != BASE_DATOS_PRUEBAS:
        pytest.fail(
            f"Prueba bloqueada: DB_NAME debe ser "
            f"'{BASE_DATOS_PRUEBAS}'."
        )

    with engine.connect() as connection:
        base_actual = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    if base_actual != BASE_DATOS_PRUEBAS:
        pytest.fail(
            "Prueba bloqueada: la conexión no apunta "
            "a la base de pruebas."
        )

    sufijo = uuid.uuid4().hex[:10]
    nombre = f"TEST_INTEGRACION_{sufijo}"
    estudiante_id = None

    try:
        datos = EstudianteCrear(
            nombre=nombre,
            curso_id=12,       # 10mo EGB
            paralelo_id=3,     # C
            especialidad_id=None,
            sexo="Masculino",
        )

        estudiante = estudiante_service.crear_estudiante(datos)
        estudiante_id = estudiante["id"]

        yield estudiante

    finally:
        if estudiante_id is not None:
            try:
                with engine.begin() as connection:
                    connection.execute(
                        text("""
                            DELETE FROM public.atencion
                            WHERE estudiante_id = :id
                        """),
                        {"id": estudiante_id},
                    )
                    connection.execute(
                        text("""
                            DELETE FROM public.estudiante
                            WHERE id = :id
                        """),
                        {"id": estudiante_id},
                    )
            except SQLAlchemyError as exc:
                pytest.fail(
                    "No se pudo limpiar el estudiante temporal "
                    f"{estudiante_id}: {exc}"
                )


def test_crear_actualizar_y_auditar_estudiante(
    estudiante_temporal,
):
    estudiante_id = estudiante_temporal["id"]

    # 1. Comprobar que el estudiante fue creado en PostgreSQL.
    estudiantes = estudiante_service.obtener_estudiantes()
    estudiante = next(
        (
            e for e in estudiantes
            if e["id"] == estudiante_id
        ),
        None,
    )

    assert estudiante is not None
    assert estudiante["nombre"] == estudiante_temporal["nombre"]
    assert estudiante["curso_id"] == 12
    assert estudiante["paralelo_id"] == 3
    assert estudiante["especialidad_id"] is None

    # 2. Actualizar usando el usuario de prueba con ID 2.
    datos_actualizados = EstudianteActualizar(
        nombre=f"{estudiante_temporal['nombre']}_EDITADO",
        curso_id=12,
        paralelo_id=3,
        especialidad_id=None,
        sexo="Femenino",
    )

    actualizado = estudiante_service.actualizar_estudiante(
        estudiante_id=estudiante_id,
        datos=datos_actualizados,
        usuario_id=2,
    )

    assert actualizado["id"] == estudiante_id
    assert actualizado["nombre"] == datos_actualizados.nombre
    assert actualizado["sexo"] == "Femenino"
    assert actualizado["modificado_por"] == 2
    assert actualizado["fecha_modificacion"] is not None

    # 3. Verificar los datos de auditoría.
    auditoria = estudiante_service.obtener_auditoria_estudiante(
        estudiante_id
    )

    assert auditoria["estudiante_id"] == estudiante_id
    assert auditoria["modificado_por"] == 2
    assert auditoria["modificado_por_nombre"] is not None
    assert auditoria["modificado_por_email"] is not None
    assert auditoria["fecha_modificacion"] is not None

def test_trigger_rechaza_bachillerato_sin_especialidad():
    # Protección: verificar la base de datos antes de escribir.
    if settings.DB_NAME != BASE_DATOS_PRUEBAS:
        pytest.fail("Prueba bloqueada: DB_NAME no es la base de pruebas.")

    with engine.connect() as connection:
        base_actual = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    if base_actual != BASE_DATOS_PRUEBAS:
        pytest.fail("Prueba bloqueada: conexión a una base incorrecta.")

    # La transacción se revierte al salir, incluso si la inserción falla.
    with engine.connect() as connection:
        transaccion = connection.begin()

        try:
            with pytest.raises(ProgrammingError, match="Bachillerato requiere especialidad"):
                connection.execute(
                    text("""
                        INSERT INTO public.estudiante (
                            nombre,
                            curso_id,
                            paralelo_id,
                            especialidad_id,
                            sexo
                        )
                        VALUES (
                            :nombre,
                            :curso_id,
                            NULL,
                            NULL,
                            :sexo
                        )
                    """),
                    {
                        "nombre": "TEST_TRIGGER_BACHILLERATO",
                        "curso_id": 13,  # 1ro Bachillerato
                        "sexo": "Masculino",
                    },
                )
        finally:
            if transaccion.is_active:
                transaccion.rollback()



def test_trigger_rechaza_egb_con_especialidad():
    assert settings.DB_NAME == BASE_DATOS_PRUEBAS

    with engine.connect() as connection:
        base_actual = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    assert base_actual == BASE_DATOS_PRUEBAS

    with engine.connect() as connection:
        transaccion = connection.begin()

        try:
            with pytest.raises(
                ProgrammingError,
                match="Inicial y EGB requieren paralelo",
            ):
                connection.execute(
                    text("""
                        INSERT INTO public.estudiante (
                            nombre,
                            curso_id,
                            paralelo_id,
                            especialidad_id,
                            sexo
                        )
                        VALUES (
                            :nombre,
                            :curso_id,
                            :paralelo_id,
                            :especialidad_id,
                            :sexo
                        )
                    """),
                    {
                        "nombre": "TEST_TRIGGER_EGB_ESPECIALIDAD",
                        "curso_id": 12,
                        "paralelo_id": 3,
                        "especialidad_id": 2,
                        "sexo": "Masculino",
                    },
                )
        finally:
            if transaccion.is_active:
                transaccion.rollback()
