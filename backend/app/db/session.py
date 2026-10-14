
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def verificar_conexion() -> dict:
    with engine.connect() as connection:
        resultado = connection.execute(
            text("SELECT current_database(), current_user")
        )
        base, usuario = resultado.one()

    return {
        "conectado": True,
        "base_datos": base,
        "usuario": usuario,
    }
