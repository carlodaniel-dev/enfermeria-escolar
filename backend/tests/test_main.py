
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

@pytest.fixture
def restaurar_dependencias():
    dependencias_originales = app.dependency_overrides.copy()

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(dependencias_originales)

def test_root():
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "en funcionamiento"


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["estado"] == "ok"


def test_catalogos_sin_token():
    response = client.get("/api/catalogos")

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "No autenticado o token inválido."
    )


def test_catalogos_con_token_invalido():
    response = client.get(
        "/api/catalogos",
        headers={"Authorization": "Bearer token-invalido-123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "No autenticado o token inválido."
    )


def test_login_correcto(monkeypatch):
    from app.api.routes import auth

    usuario_falso = {
        "access_token": "token-de-prueba",
        "token_type": "bearer",
        "usuario_id": 1,
        "nombre": "Administrador de prueba",
        "email": "admin@enfermeria.local",
        "rol": "Admin",
    }

    def autenticar_falso(email, password):
        return usuario_falso

    monkeypatch.setattr(
        auth,
        "autenticar_usuario",
        autenticar_falso,
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@enfermeria.local",
            "password": "contraseña-de-prueba",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "token-de-prueba"
    assert data["token_type"] == "bearer"
    assert data["rol"] == "Admin"


def test_login_con_credenciales_incorrectas(monkeypatch):
    from app.api.routes import auth

    def autenticar_falso(email, password):
        return None

    monkeypatch.setattr(
        auth,
        "autenticar_usuario",
        autenticar_falso,
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@enfermeria.local",
            "password": "incorrecta",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Correo o contraseña incorrectos."
    )


def test_login_usuario_inactivo(monkeypatch):
    from app.api.routes import auth

    def autenticar_falso(email, password):
        return None

    monkeypatch.setattr(
        auth,
        "autenticar_usuario",
        autenticar_falso,
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "usuario@enfermeria.local",
            "password": "contraseña-de-prueba",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Correo o contraseña incorrectos."
    )


def test_modificar_atencion_sin_permisos(monkeypatch, restaurar_dependencias):
    from app.api.routes import atenciones

    def usuario_falso():
        return {
            "id": 2,
            "nombre": "Usuario de prueba",
            "email": "usuario@enfermeria.local",
            "rol": "Usuario",
            "activo": True,
        }

    def actualizar_falso(**kwargs):
        raise PermissionError(
            "Solo puedes modificar tus propias atenciones."
        )

    monkeypatch.setattr(
        atenciones,
        "actualizar_atencion",
        actualizar_falso,
    )
    app.dependency_overrides[
        atenciones.obtener_usuario_actual
    ] = usuario_falso

    response = client.put(
        "/api/atenciones/8",
        json={
            "saturacion": 98,
            "frecuencia_cardiaca": 80,
            "temperatura": 36.5,
            "diagnostico_id": 1,
            "descripcion_diagnostico": None,
            "recomendacion": "Reposo",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Solo puedes modificar tus propias atenciones."
    )


def test_modificar_atencion_inexistente(monkeypatch, restaurar_dependencias):
    from app.api.routes import atenciones

    def usuario_falso():
        return {
            "id": 1,
            "nombre": "Administrador de prueba",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        }

    def actualizar_falso(**kwargs):
        raise LookupError("La atención no existe.")

    monkeypatch.setattr(
        atenciones,
        "actualizar_atencion",
        actualizar_falso,
    )
    app.dependency_overrides[
        atenciones.obtener_usuario_actual
    ] = usuario_falso

    response = client.put(
        "/api/atenciones/999999",
        json={
            "saturacion": 98,
            "frecuencia_cardiaca": 80,
            "temperatura": 36.5,
            "diagnostico_id": 1,
            "descripcion_diagnostico": None,
            "recomendacion": "Reposo",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "La atención no existe."


def test_modificar_atencion_id_no_positivo(restaurar_dependencias):
    from app.core.dependencies import obtener_usuario_actual

    def usuario_falso():
        return {
            "id": 1,
            "nombre": "Administrador de prueba",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        }

    app.dependency_overrides[obtener_usuario_actual] = usuario_falso

    response = client.put(
        "/api/atenciones/0",
        json={
            "saturacion": 98,
            "frecuencia_cardiaca": 80,
            "temperatura": 36.5,
            "diagnostico_id": 1,
            "descripcion_diagnostico": None,
            "recomendacion": "Reposo",
        },
    )

    assert response.status_code == 422


def test_auditoria_estudiante_sin_autenticacion():
    response = client.get(
        "/api/estudiantes/1/auditoria",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "No autenticado o token inválido."
    )


def test_auditoria_estudiante_usuario_sin_permisos(restaurar_dependencias):
    from app.core.dependencies import exigir_admin, obtener_usuario_actual

    def usuario_falso():
        return {
            "id": 2,
            "nombre": "Usuario de prueba",
            "email": "usuario@enfermeria.local",
            "rol": "Usuario",
            "activo": True,
        }

    # Simulamos un usuario autenticado con rol Usuario.
    app.dependency_overrides[obtener_usuario_actual] = usuario_falso

    response = client.get(
        "/api/estudiantes/1/auditoria",
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "No tienes permisos para realizar esta acción."
    )


def test_auditoria_estudiante_admin_autorizado(monkeypatch, restaurar_dependencias):
    from app.api.routes import estudiantes
    from app.core.dependencies import exigir_admin

    auditoria_falsa = {
        "estudiante_id": 1,
        "estudiante": "Estudiante de prueba",
        "modificado_por": 1,
        "modificado_por_nombre": "Administrador de prueba",
        "modificado_por_email": "admin@enfermeria.local",
        "fecha_modificacion": "2026-10-19T10:00:00",
    }

    def usuario_falso():
        return {
            "id": 1,
            "nombre": "Administrador de prueba",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        }

    def auditoria_falsa_funcion(estudiante_id):
        assert estudiante_id == 1
        return auditoria_falsa

    monkeypatch.setattr(
        estudiantes,
        "obtener_auditoria_estudiante",
        auditoria_falsa_funcion,
    )
    app.dependency_overrides[exigir_admin] = usuario_falso

    response = client.get(
        "/api/estudiantes/1/auditoria",
    )

    assert response.status_code == 200
    assert response.json()["estudiante_id"] == 1
    assert response.json()["modificado_por_nombre"] == (
        "Administrador de prueba"
    )


def test_auditoria_estudiante_inexistente(monkeypatch, restaurar_dependencias):
    from app.api.routes import estudiantes
    from app.core.dependencies import exigir_admin

    def usuario_falso():
        return {
            "id": 1,
            "nombre": "Administrador de prueba",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        }

    def auditoria_falsa_funcion(estudiante_id):
        raise LookupError("El estudiante no existe.")

    monkeypatch.setattr(
        estudiantes,
        "obtener_auditoria_estudiante",
        auditoria_falsa_funcion,
    )
    app.dependency_overrides[exigir_admin] = usuario_falso

    response = client.get(
        "/api/estudiantes/999999/auditoria",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "El estudiante no existe."
    )


def test_modificar_estudiante_inexistente(monkeypatch, restaurar_dependencias):
    from app.api.routes import estudiantes
    from app.core.dependencies import obtener_usuario_actual

    def usuario_falso():
        return {
            "id": 1,
            "nombre": "Administrador",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        }

    def actualizar_falso(**kwargs):
        raise LookupError("El estudiante no existe.")

    monkeypatch.setattr(
        estudiantes,
        "actualizar_estudiante",
        actualizar_falso,
    )
    app.dependency_overrides[obtener_usuario_actual] = usuario_falso

    response = client.put(
        "/api/estudiantes/999999",
        json={
            "nombre": "Estudiante de prueba",
            "curso_id": 12,
            "paralelo_id": 3,
            "especialidad_id": None,
            "sexo": "Masculino",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "El estudiante no existe."


def test_modificar_estudiante_curso_inexistente(monkeypatch, restaurar_dependencias):
    from app.api.routes import estudiantes
    from app.core.dependencies import obtener_usuario_actual

    def usuario_falso():
        return {
            "id": 1,
            "nombre": "Administrador",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        }

    def actualizar_falso(**kwargs):
        raise ValueError("El curso seleccionado no existe.")

    monkeypatch.setattr(
        estudiantes,
        "actualizar_estudiante",
        actualizar_falso,
    )
    app.dependency_overrides[obtener_usuario_actual] = usuario_falso

    response = client.put(
        "/api/estudiantes/3",
        json={
            "nombre": "Estudiante de prueba",
            "curso_id": 999999,
            "paralelo_id": 3,
            "especialidad_id": None,
            "sexo": "Masculino",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "El curso seleccionado no existe."
    )


def test_modificar_estudiante_egb_sin_paralelo(monkeypatch, restaurar_dependencias):
    from app.api.routes import estudiantes
    from app.core.dependencies import obtener_usuario_actual

    def usuario_falso():
        return {
            "id": 1,
            "nombre": "Administrador",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        }

    def actualizar_falso(**kwargs):
        raise ValueError("Inicial y EGB requieren un paralelo.")

    monkeypatch.setattr(
        estudiantes,
        "actualizar_estudiante",
        actualizar_falso,
    )
    app.dependency_overrides[obtener_usuario_actual] = usuario_falso

    response = client.put(
        "/api/estudiantes/3",
        json={
            "nombre": "Estudiante de prueba",
            "curso_id": 12,
            "paralelo_id": None,
            "especialidad_id": None,
            "sexo": "Masculino",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Inicial y EGB requieren un paralelo."
    )


def test_modificar_estudiante_bachillerato_sin_especialidad(monkeypatch, restaurar_dependencias):
    from app.api.routes import estudiantes
    from app.core.dependencies import obtener_usuario_actual

    def usuario_falso():
        return {
            "id": 1,
            "nombre": "Administrador",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        }

    def actualizar_falso(**kwargs):
        raise ValueError("Bachillerato requiere una especialidad.")

    monkeypatch.setattr(
        estudiantes,
        "actualizar_estudiante",
        actualizar_falso,
    )
    app.dependency_overrides[obtener_usuario_actual] = usuario_falso

    response = client.put(
        "/api/estudiantes/3",
        json={
            "nombre": "Estudiante de prueba",
            "curso_id": 20,
            "paralelo_id": None,
            "especialidad_id": None,
            "sexo": "Masculino",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Bachillerato requiere una especialidad."
    )


def test_exigir_admin_rechaza_usuario_normal():
    from fastapi import HTTPException
    from app.core.dependencies import exigir_admin

    usuario = {
        "id": 2,
        "nombre": "Usuario de prueba",
        "email": "usuario@enfermeria.local",
        "rol": "Usuario",
        "activo": True,
    }

    with pytest.raises(HTTPException) as error:
        exigir_admin(usuario=usuario)

    assert error.value.status_code == 403
    assert error.value.detail == (
        "No tienes permisos para realizar esta acción."
    )


def test_exigir_admin_permite_administrador():
    from app.core.dependencies import exigir_admin

    usuario = {
        "id": 1,
        "nombre": "Administrador de prueba",
        "email": "admin@enfermeria.local",
        "rol": "Admin",
        "activo": True,
    }

    resultado = exigir_admin(usuario=usuario)

    assert resultado == usuario


@pytest.mark.parametrize(
    "usuario",
    [
        {
            "id": 1,
            "nombre": "Administrador de prueba",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        },
        {
            "id": 2,
            "nombre": "Usuario de prueba",
            "email": "usuario@enfermeria.local",
            "rol": "Usuario",
            "activo": True,
        },
    ],
    ids=["admin", "usuario"],
)
def test_registrar_estudiante_permitido(
    usuario,
    monkeypatch,
    restaurar_dependencias,
):
    from app.api.routes import estudiantes
    from app.core.dependencies import obtener_usuario_actual

    estudiante_falso = {
        "id": 100,
        "nombre": "Estudiante de prueba",
        "curso_id": 12,
        "paralelo_id": 3,
        "especialidad_id": None,
        "sexo": "Masculino",
    }

    def usuario_falso():
        return usuario

    def crear_falso(datos):
        return estudiante_falso

    monkeypatch.setattr(
        estudiantes,
        "crear_estudiante",
        crear_falso,
    )
    app.dependency_overrides[obtener_usuario_actual] = usuario_falso

    response = client.post(
        "/api/estudiantes",
        json={
            "nombre": "Estudiante de prueba",
            "curso_id": 12,
            "paralelo_id": 3,
            "especialidad_id": None,
            "sexo": "Masculino",
        },
    )

    assert response.status_code == 201
    assert response.json()["nombre"] == "Estudiante de prueba"
    assert response.json()["id"] == 100


def test_registrar_estudiante_sin_autenticacion():
    response = client.post(
        "/api/estudiantes",
        json={
            "nombre": "Estudiante de prueba",
            "curso_id": 12,
            "paralelo_id": 3,
            "especialidad_id": None,
            "sexo": "Masculino",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "No autenticado o token inválido."
    )


@pytest.mark.parametrize(
    "usuario",
    [
        {
            "id": 1,
            "nombre": "Administrador de prueba",
            "email": "admin@enfermeria.local",
            "rol": "Admin",
            "activo": True,
        },
        {
            "id": 2,
            "nombre": "Usuario de prueba",
            "email": "usuario@enfermeria.local",
            "rol": "Usuario",
            "activo": True,
        },
    ],
    ids=["admin", "usuario"],
)
def test_modificar_estudiante_permitido(
    usuario,
    monkeypatch,
    restaurar_dependencias,
):
    from app.api.routes import estudiantes
    from app.core.dependencies import obtener_usuario_actual

    estudiante_falso = {
        "id": 3,
        "nombre": "Estudiante actualizado",
        "curso_id": 12,
        "paralelo_id": 3,
        "especialidad_id": None,
        "sexo": "Masculino",
    }

    def usuario_falso():
        return usuario

    def actualizar_falso(**kwargs):
        assert kwargs["estudiante_id"] == 3
        assert kwargs["usuario_id"] == usuario["id"]
        return estudiante_falso

    monkeypatch.setattr(
        estudiantes,
        "actualizar_estudiante",
        actualizar_falso,
    )
    app.dependency_overrides[obtener_usuario_actual] = usuario_falso

    response = client.put(
        "/api/estudiantes/3",
        json={
            "nombre": "Estudiante actualizado",
            "curso_id": 12,
            "paralelo_id": 3,
            "especialidad_id": None,
            "sexo": "Masculino",
        },
    )

    assert response.status_code == 200
    assert response.json()["nombre"] == "Estudiante actualizado"


def test_modificar_estudiante_sin_autenticacion():
    response = client.put(
        "/api/estudiantes/3",
        json={
            "nombre": "Estudiante actualizado",
            "curso_id": 12,
            "paralelo_id": 3,
            "especialidad_id": None,
            "sexo": "Masculino",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "No autenticado o token inválido."
    )
