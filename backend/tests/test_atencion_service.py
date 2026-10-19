
from contextlib import contextmanager

import pytest

from app.schemas.atencion import AtencionActualizar, AtencionCrear
from app.services import atencion_service


class ResultadoFalso:
    def __init__(self, fila=None, filas=None):
        self.fila = fila
        self.filas = filas if filas is not None else (
            [] if fila is None else [fila]
        )

    def mappings(self):
        return self

    def first(self):
        return self.fila

    def one(self):
        if self.fila is None:
            raise AssertionError("No existe una fila para devolver.")
        return self.fila

    def all(self):
        return self.filas


class ConexionFalsa:
    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.consultas = []
        self.parametros = []

    
    def execute(self, consulta, parametros=None):
        sql = str(consulta)
        self.consultas.append(sql)
        self.parametros.append(parametros or {})

        if "FROM public.atencion" in sql and "FOR UPDATE" in sql:
            return ResultadoFalso(self.respuestas.get("atencion"))

        if "FROM public.estudiante" in sql:
            return ResultadoFalso(self.respuestas.get("estudiante"))

        if "FROM public.usuario" in sql:
            return ResultadoFalso(self.respuestas.get("usuario"))

        if "FROM public.diagnostico" in sql:
            return ResultadoFalso(self.respuestas.get("diagnostico"))

        if "UPDATE public.atencion" in sql:
            return ResultadoFalso(self.respuestas.get("actualizada"))

        if "INSERT INTO public.atencion" in sql:
            return ResultadoFalso(self.respuestas.get("creada"))

        raise AssertionError(f"Consulta SQL inesperada: {sql}")


class MotorFalso:
    def __init__(self, respuestas):
        self.conexion = ConexionFalsa(respuestas)

    @contextmanager
    def begin(self):
        yield self.conexion


def datos_atencion():
    return AtencionActualizar(
        saturacion=98,
        frecuencia_cardiaca=80,
        temperatura=36.5,
        diagnostico_id=1,
        descripcion_diagnostico=None,
        recomendacion="Reposo",
    )


def usuario(id_usuario, rol):
    return {
        "id": id_usuario,
        "rol": rol,
    }


def test_usuario_no_puede_modificar_atencion_de_otro_usuario(
    monkeypatch,
):
    motor = MotorFalso({
        "atencion": {"id": 8, "usuario_id": 1},
    })
    monkeypatch.setattr(atencion_service, "engine", motor)

    with pytest.raises(
        PermissionError,
        match="Solo puedes modificar tus propias atenciones",
    ):
        atencion_service.actualizar_atencion(
            atencion_id=8,
            datos=datos_atencion(),
            usuario_actual=usuario(2, "Usuario"),
        )

    assert len(motor.conexion.consultas) == 1
    assert "FOR UPDATE" in motor.conexion.consultas[0]
    assert not any(
        "UPDATE public.atencion" in sql
        for sql in motor.conexion.consultas
    )


@pytest.mark.parametrize(
    ("usuario_actual", "creador_id"),
    [
        ({"id": 1, "rol": "Admin"}, 2),
        ({"id": 2, "rol": "Usuario"}, 2),
    ],
    ids=["administrador-modifica-atencion-ajena", "usuario-modifica-atencion-propia"],
)
def test_actualizar_atencion_permitida(
    monkeypatch,
    usuario_actual,
    creador_id,
):
    fila_actualizada = {
        "id": 8,
        "estudiante_id": 3,
        "fecha_hora": "2026-10-19T09:00:00",
        "saturacion": 98,
        "frecuencia_cardiaca": 80,
        "temperatura": 36.5,
        "diagnostico_id": 1,
        "descripcion_diagnostico": None,
        "recomendacion": "Reposo",
        "usuario_id": creador_id,
        "modificado_por": usuario_actual["id"],
        "fecha_modificacion": "2026-10-19T10:00:00",
    }

    motor = MotorFalso({
        "atencion": {"id": 8, "usuario_id": creador_id},
        "diagnostico": {"nombre": "Golpe"},
        "actualizada": fila_actualizada,
    })
    monkeypatch.setattr(atencion_service, "engine", motor)

    resultado = atencion_service.actualizar_atencion(
        atencion_id=8,
        datos=datos_atencion(),
        usuario_actual=usuario_actual,
    )

    assert resultado["id"] == 8
    assert resultado["modificado_por"] == usuario_actual["id"]

    # Se conserva el usuario que registró originalmente la atención.
    assert resultado["usuario_id"] == creador_id

    consulta_update = next(
        sql
        for sql in motor.conexion.consultas
        if "UPDATE public.atencion" in sql
    )
    parametros_update = next(
        parametros
        for sql, parametros in zip(
            motor.conexion.consultas,
            motor.conexion.parametros,
        )
        if "UPDATE public.atencion" in sql
    )

    assert "usuario_id =" not in consulta_update
    assert "fecha_hora =" not in consulta_update
    assert parametros_update["modificado_por"] == usuario_actual["id"]
    assert parametros_update["id"] == 8


def test_actualizar_atencion_inexistente(monkeypatch):
    motor = MotorFalso({"atencion": None})
    monkeypatch.setattr(atencion_service, "engine", motor)

    with pytest.raises(
        LookupError,
        match="La atención no existe",
    ):
        atencion_service.actualizar_atencion(
            atencion_id=999999,
            datos=datos_atencion(),
            usuario_actual=usuario(1, "Admin"),
        )

    assert len(motor.conexion.consultas) == 1
    assert not any(
        "UPDATE public.atencion" in sql
        for sql in motor.conexion.consultas
    )


def datos_nueva_atencion(**cambios):
    datos = {
        "estudiante_id": 3,
        "saturacion": 98,
        "frecuencia_cardiaca": 80,
        "temperatura": 36.5,
        "diagnostico_id": 1,
        "descripcion_diagnostico": None,
        "recomendacion": "Reposo",
    }
    datos.update(cambios)
    return AtencionCrear(**datos)


def motor_para_crear_atencion(**cambios):
    respuestas = {
        "estudiante": {"id": 3},
        "usuario": {"id": 1},
        "diagnostico": {"nombre": "Golpe"},
        "creada": {
            "id": 15,
            "estudiante_id": 3,
            "fecha_hora": "2026-10-19T09:00:00",
            "saturacion": 98,
            "frecuencia_cardiaca": 80,
            "temperatura": 36.5,
            "diagnostico_id": 1,
            "descripcion_diagnostico": None,
            "recomendacion": "Reposo",
            "usuario_id": 1,
            "modificado_por": None,
            "fecha_modificacion": None,
        },
    }
    respuestas.update(cambios)
    return MotorFalso(respuestas)


def test_crear_atencion_estudiante_inexistente(monkeypatch):
    motor = motor_para_crear_atencion(estudiante=None)
    monkeypatch.setattr(atencion_service, "engine", motor)

    with pytest.raises(ValueError, match="El estudiante seleccionado no existe"):
        atencion_service.crear_atencion(datos_nueva_atencion(), usuario_id=1)

    assert len(motor.conexion.consultas) == 1
    assert not any(
        "INSERT INTO public.atencion" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_atencion_usuario_inactivo_o_inexistente(monkeypatch):
    motor = motor_para_crear_atencion(usuario=None)
    monkeypatch.setattr(atencion_service, "engine", motor)

    with pytest.raises(ValueError, match="El usuario no existe o está inactivo"):
        atencion_service.crear_atencion(datos_nueva_atencion(), usuario_id=1)

    assert not any(
        "INSERT INTO public.atencion" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_atencion_diagnostico_inactivo_o_inexistente(monkeypatch):
    motor = motor_para_crear_atencion(diagnostico=None)
    monkeypatch.setattr(atencion_service, "engine", motor)

    with pytest.raises(
        ValueError,
        match="El diagnóstico no existe o está inactivo",
    ):
        atencion_service.crear_atencion(datos_nueva_atencion(), usuario_id=1)

    assert not any(
        "INSERT INTO public.atencion" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_atencion_otros_sin_descripcion(monkeypatch):
    motor = motor_para_crear_atencion(
        diagnostico={"nombre": "Otros"},
    )
    monkeypatch.setattr(atencion_service, "engine", motor)

    with pytest.raises(
        ValueError,
        match="Debes describir el diagnóstico cuando seleccionas Otros",
    ):
        atencion_service.crear_atencion(datos_nueva_atencion(), usuario_id=1)

    assert not any(
        "INSERT INTO public.atencion" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_atencion_otro_diagnostico_con_descripcion(monkeypatch):
    motor = motor_para_crear_atencion()
    monkeypatch.setattr(atencion_service, "engine", motor)

    with pytest.raises(
        ValueError,
        match="La descripción adicional solo se permite",
    ):
        atencion_service.crear_atencion(
            datos_nueva_atencion(descripcion_diagnostico="Detalle adicional"),
            usuario_id=1,
        )

    assert not any(
        "INSERT INTO public.atencion" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_atencion_correctamente(monkeypatch):
    motor = motor_para_crear_atencion()
    monkeypatch.setattr(atencion_service, "engine", motor)

    resultado = atencion_service.crear_atencion(
        datos_nueva_atencion(),
        usuario_id=1,
    )

    assert resultado["id"] == 15
    assert resultado["estudiante_id"] == 3
    assert resultado["usuario_id"] == 1

    consulta_insert = next(
        sql
        for sql in motor.conexion.consultas
        if "INSERT INTO public.atencion" in sql
    )
    parametros_insert = next(
        parametros
        for sql, parametros in zip(
            motor.conexion.consultas,
            motor.conexion.parametros,
        )
        if "INSERT INTO public.atencion" in sql
    )

    assert "RETURNING" in consulta_insert
    assert parametros_insert["estudiante_id"] == 3
    assert parametros_insert["usuario_id"] == 1
    assert parametros_insert["diagnostico_id"] == 1



def test_crear_atencion_normaliza_descripcion_de_otros(monkeypatch):
    motor = motor_para_crear_atencion(
        diagnostico={"nombre": "Otros"},
        creada={
            **motor_para_crear_atencion().conexion.respuestas["creada"],
            "descripcion_diagnostico": "Dolor persistente",
        },
    )
    monkeypatch.setattr(atencion_service, "engine", motor)

    resultado = atencion_service.crear_atencion(
        datos_nueva_atencion(
            descripcion_diagnostico="  Dolor persistente  ",
        ),
        usuario_id=1,
    )

    assert resultado["descripcion_diagnostico"] == "Dolor persistente"

    parametros_insert = next(
        parametros
        for sql, parametros in zip(
            motor.conexion.consultas,
            motor.conexion.parametros,
        )
        if "INSERT INTO public.atencion" in sql
    )
    assert parametros_insert["descripcion_diagnostico"] == "Dolor persistente"
