
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import text

from app.core.config import settings
from app.core.security import verify_password
from app.db.session import engine


def autenticar_usuario(email: str, password: str) -> dict | None:
    consulta = text("""
        SELECT
            u.id,
            u.nombre,
            u.email,
            u.rol,
            u.activo,
            c.password_hash
        FROM usuario AS u
        INNER JOIN usuario_credencial AS c
            ON c.usuario_id = u.id
        WHERE LOWER(u.email) = LOWER(:email)
        LIMIT 1
    """)

    with engine.connect() as connection:
        usuario = connection.execute(
            consulta,
            {"email": email.strip()},
        ).mappings().first()

    if usuario is None or not usuario["activo"]:
        return None

    if not verify_password(password, usuario["password_hash"]):
        return None

    ahora = datetime.now(timezone.utc)
    expiracion = ahora + timedelta(minutes=30)

    token = jwt.encode(
        {
            "sub": str(usuario["id"]),
            "iat": ahora,
            "exp": expiracion,
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario_id": usuario["id"],
        "nombre": usuario["nombre"],
        "email": usuario["email"],
        "rol": usuario["rol"],
    }
