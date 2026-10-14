
from getpass import getpass

from sqlalchemy import text

from app.core.security import hash_password
from app.db.session import engine


def main():
    email = input("Correo del usuario: ").strip()
    password = getpass("Nueva contraseña: ")
    confirmacion = getpass("Confirma la contraseña: ")

    if not email or not password:
        print("Error: el correo y la contraseña son obligatorios.")
        return

    if password != confirmacion:
        print("Error: las contraseñas no coinciden.")
        return

    if len(password) < 8:
        print("Error: utiliza al menos 8 caracteres.")
        return

    with engine.begin() as connection:
        usuario = connection.execute(
            text("""
                SELECT id, nombre, email, rol
                FROM usuario
                WHERE LOWER(email) = LOWER(:email)
                    AND activo = TRUE
            """),
            {"email": email},
        ).mappings().first()

        if usuario is None:
            print("Error: no existe un usuario activo con ese correo.")
            return

        existente = connection.execute(
            text("""
                SELECT usuario_id
                FROM usuario_credencial
                WHERE usuario_id = :usuario_id
            """),
            {"usuario_id": usuario["id"]},
        ).first()

        if existente:
            print("Este usuario ya tiene credenciales. No se modificaron.")
            return

        connection.execute(
            text("""
                INSERT INTO usuario_credencial (usuario_id, password_hash)
                VALUES (:usuario_id, :password_hash)
            """),
            {
                "usuario_id": usuario["id"],
                "password_hash": hash_password(password),
            },
        )

    print(f"Credenciales creadas para: {usuario['email']}")
    print(f"Rol: {usuario['rol']}")


if __name__ == "__main__":
    main()
