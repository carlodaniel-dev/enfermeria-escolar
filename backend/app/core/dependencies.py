
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
import jwt

from app.core.config import settings
from app.core.security import verificar_access_token
from app.db.session import engine

bearer_scheme = HTTPBearer(auto_error=False)


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if credenciales is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado o token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verificar_access_token(credenciales.credentials)
        subject = payload.get("sub")

        if not subject:
            raise error

        usuario_id = int(subject)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error

    with engine.connect() as connection:
        usuario = connection.execute(
            text("""
                SELECT id, nombre, email, rol, activo
                FROM usuario
                WHERE id = :usuario_id
            """),
            {"usuario_id": usuario_id},
        ).mappings().first()

    if usuario is None or not usuario["activo"]:
        raise error

    return dict(usuario)


def exigir_admin(
    usuario: dict = Depends(obtener_usuario_actual),
) -> dict:
    if usuario["rol"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción.",
        )

    return usuario
