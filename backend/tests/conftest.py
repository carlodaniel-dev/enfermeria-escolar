
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import engine


BASE_DATOS_PRUEBAS = "enfermeria_escolar"


def verificar_base_de_datos():
    """Impide ejecutar pruebas contra una base distinta de la de pruebas."""

    # Primera barrera: comprobar la configuración cargada.
    if settings.DB_NAME != BASE_DATOS_PRUEBAS:
        pytest.exit(
            "SEGURIDAD: DB_NAME debe ser "
            f"'{BASE_DATOS_PRUEBAS}', pero está configurada como "
            f"'{settings.DB_NAME}'. No se ejecutarán las pruebas.",
            returncode=2,
        )

    # Segunda barrera: comprobar la URL del motor SQLAlchemy.
    if engine.url.database != BASE_DATOS_PRUEBAS:
        pytest.exit(
            "SEGURIDAD: el motor SQLAlchemy apunta a una base "
            "distinta de la base de pruebas. "
            "No se ejecutarán las pruebas.",
            returncode=2,
        )

    # Tercera barrera: consultar la base real de la conexión.
    try:
        with engine.connect() as connection:
            base_actual = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

    except SQLAlchemyError:
        pytest.exit(
            "SEGURIDAD: no se pudo verificar la base de datos. "
            "Comprueba PostgreSQL y la configuración de conexión. "
            "No se ejecutarán las pruebas.",
            returncode=2,
        )

    if base_actual != BASE_DATOS_PRUEBAS:
        pytest.exit(
            "SEGURIDAD: PostgreSQL confirmó una base distinta "
            "de la base de pruebas. No se ejecutarán las pruebas.",
            returncode=2,
        )


def pytest_sessionstart(session):
    """Valida la conexión antes de comenzar la sesión de pruebas."""
    verificar_base_de_datos()
