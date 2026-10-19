
from contextlib import contextmanager

import pytest

from app.schemas.estudiante import EstudianteActualizar, EstudianteCrear
from app.services import estudiante_service



class ResultadoFalso:
    """Simula un resultado de SQLAlchemy."""

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
    """Simula consultas sin conectarse a PostgreSQL."""

    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.consultas = []
        self.parametros = []

    def execute(self, consulta, parametros=None):
        sql = str(consulta)
        self.consultas.append(sql)
        self.parametros.append(parametros or {})

        if "INSERT INTO public.estudiante" in sql:
            return ResultadoFalso(
                self.respuestas.get("insert")
            )

        if "UPDATE public.estudiante" in sql:
            return ResultadoFalso(
                self.respuestas.get("update")
            )

        if "FROM public.estudiante" in sql:
            if "WHERE id = :estudiante_id" in sql:
                return ResultadoFalso(
                    self.respuestas.get("estudiante")
                )

            if "WHERE e.id = :id" in sql:
                return ResultadoFalso(
                    self.respuestas.get("resultado")
                )

        if "FROM public.curso" in sql:
            return ResultadoFalso(
                self.respuestas.get("curso")
            )

        if "FROM public.paralelo" in sql:
            return ResultadoFalso(
                self.respuestas.get("paralelo")
            )

        if "FROM public.especialidad" in sql:
            return ResultadoFalso(
                self.respuestas.get("especialidad")
            )

        raise AssertionError(
            f"Consulta SQL inesperada en esta prueba: {sql}"
        )


class MotorFalso:
    """Proporciona una conexión simulada para engine.begin()."""

    def __init__(self, respuestas):
        self.conexion = ConexionFalsa(respuestas)

    @contextmanager
    def begin(self):
        yield self.conexion


def datos_estudiante(
    nombre="Estudiante de prueba",
    curso_id=12,
    paralelo_id=3,
    especialidad_id=None,
):
    return EstudianteCrear(
        nombre=nombre,
        curso_id=curso_id,
        paralelo_id=paralelo_id,
        especialidad_id=especialidad_id,
        sexo="Masculino",
    )


def test_crear_estudiante_curso_inexistente(monkeypatch):
    motor = MotorFalso({"curso": None})
    monkeypatch.setattr(estudiante_service, "engine", motor)

    with pytest.raises(
        ValueError,
        match="El curso seleccionado no existe",
    ):
        estudiante_service.crear_estudiante(
            datos_estudiante(curso_id=999999)
        )

    assert not any(
        "INSERT INTO public.estudiante" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_estudiante_egb_sin_paralelo(monkeypatch):
    motor = MotorFalso({
        "curso": {"nivel": "EGB"},
    })
    monkeypatch.setattr(estudiante_service, "engine", motor)

    with pytest.raises(
        ValueError,
        match="Inicial y EGB requieren un paralelo",
    ):
        estudiante_service.crear_estudiante(
            datos_estudiante(paralelo_id=None)
        )

    assert not any(
        "INSERT INTO public.estudiante" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_estudiante_bachillerato_sin_especialidad(monkeypatch):
    motor = MotorFalso({
        "curso": {"nivel": "Bachillerato"},
    })
    monkeypatch.setattr(estudiante_service, "engine", motor)

    with pytest.raises(
        ValueError,
        match="Bachillerato requiere una especialidad",
    ):
        estudiante_service.crear_estudiante(
            datos_estudiante(
                paralelo_id=None,
                especialidad_id=None,
            )
        )

    assert not any(
        "INSERT INTO public.estudiante" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_estudiante_paralelo_inexistente(monkeypatch):
    motor = MotorFalso({
        "curso": {"nivel": "EGB"},
        "paralelo": None,
    })
    monkeypatch.setattr(estudiante_service, "engine", motor)

    with pytest.raises(
        ValueError,
        match="El paralelo seleccionado no existe",
    ):
        estudiante_service.crear_estudiante(
            datos_estudiante(paralelo_id=999999)
        )

    assert not any(
        "INSERT INTO public.estudiante" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_estudiante_especialidad_inexistente(monkeypatch):
    motor = MotorFalso({
        "curso": {"nivel": "Bachillerato"},
        "especialidad": None,
    })
    monkeypatch.setattr(estudiante_service, "engine", motor)

    with pytest.raises(
        ValueError,
        match="La especialidad seleccionada no existe",
    ):
        estudiante_service.crear_estudiante(
            datos_estudiante(
                curso_id=20,
                paralelo_id=None,
                especialidad_id=999999,
            )
        )

    assert not any(
        "INSERT INTO public.estudiante" in sql
        for sql in motor.conexion.consultas
    )


def test_actualizar_estudiante_inexistente(monkeypatch):
    motor = MotorFalso({"estudiante": None})
    monkeypatch.setattr(estudiante_service, "engine", motor)

    datos = EstudianteActualizar(
        nombre="Estudiante de prueba",
        curso_id=12,
        paralelo_id=3,
        especialidad_id=None,
        sexo="Masculino",
    )

    with pytest.raises(
        LookupError,
        match="El estudiante no existe",
    ):
        estudiante_service.actualizar_estudiante(
            estudiante_id=999999,
            datos=datos,
            usuario_id=1,
        )

    assert not any(
        "UPDATE public.estudiante" in sql
        for sql in motor.conexion.consultas
    )


def test_crear_estudiante_nombre_vacio():
    with pytest.raises(
        ValueError,
        match="El nombre es obligatorio",
    ):
        estudiante_service.crear_estudiante(
            datos_estudiante(nombre="   ")
        )



def test_actualizar_estudiante_nombre_vacio():
    motor = MotorFalso({})
    datos = object.__new__(EstudianteActualizar)

    object.__setattr__(datos, "nombre", "   ")
    object.__setattr__(datos, "curso_id", 12)
    object.__setattr__(datos, "paralelo_id", 3)
    object.__setattr__(datos, "especialidad_id", None)
    object.__setattr__(datos, "sexo", "Masculino")

    with pytest.raises(
        ValueError,
        match="El nombre es obligatorio",
    ):
        estudiante_service.actualizar_estudiante(
            estudiante_id=1,
            datos=datos,
            usuario_id=1,
        )

    assert motor.conexion.consultas == []


def test_crear_estudiante_exitosamente(monkeypatch):
    estudiante = {
        "id": 50,
        "nombre": "Estudiante de prueba",
        "curso_id": 12,
        "curso": "10mo EGB",
        "nivel": "EGB",
        "paralelo_id": 3,
        "paralelo": "C",
        "especialidad_id": None,
        "especialidad": None,
        "sexo": "Masculino",
    }

    motor = MotorFalso({
        "curso": {"nivel": "EGB"},
        "paralelo": {"id": 3},
        "insert": {"id": 50},
        "resultado": estudiante,
    })
    monkeypatch.setattr(estudiante_service, "engine", motor)

    resultado = estudiante_service.crear_estudiante(
        datos_estudiante(nombre="  Estudiante de prueba  ")
    )

    assert resultado["id"] == 50
    assert resultado["nombre"] == "Estudiante de prueba"
    assert resultado["curso_id"] == 12
    assert resultado["paralelo_id"] == 3
    assert resultado["sexo"] == "Masculino"

    assert any(
        "INSERT INTO public.estudiante" in sql
        for sql in motor.conexion.consultas
    )

    parametros_insert = next(
        parametros
        for sql, parametros in zip(
            motor.conexion.consultas,
            motor.conexion.parametros,
        )
        if "INSERT INTO public.estudiante" in sql
    )

    assert parametros_insert["nombre"] == "Estudiante de prueba"


def test_actualizar_estudiante_exitosamente(monkeypatch):
    estudiante_actualizado = {
        "id": 50,
        "nombre": "Estudiante actualizado",
        "curso_id": 12,
        "curso": "10mo EGB",
        "nivel": "EGB",
        "paralelo_id": 3,
        "paralelo": "C",
        "especialidad_id": None,
        "especialidad": None,
        "sexo": "Masculino",
        "modificado_por": 2,
        "fecha_modificacion": None,
    }

    motor = MotorFalso({
        "estudiante": {"id": 50},
        "curso": {"nivel": "EGB"},
        "paralelo": {"id": 3},
        "update": {"id": 50},
        "resultado": estudiante_actualizado,
    })
    monkeypatch.setattr(estudiante_service, "engine", motor)

    datos = EstudianteActualizar(
        nombre="Estudiante actualizado",
        curso_id=12,
        paralelo_id=3,
        especialidad_id=None,
        sexo="Masculino",
    )

    resultado = estudiante_service.actualizar_estudiante(
        estudiante_id=50,
        datos=datos,
        usuario_id=2,
    )

    assert resultado["id"] == 50
    assert resultado["nombre"] == "Estudiante actualizado"
    assert resultado["modificado_por"] == 2

    assert any(
        "UPDATE public.estudiante" in sql
        for sql in motor.conexion.consultas
    )

    parametros_update = next(
        parametros
        for sql, parametros in zip(
            motor.conexion.consultas,
            motor.conexion.parametros,
        )
        if "UPDATE public.estudiante" in sql
    )

    assert parametros_update["estudiante_id"] == 50
    assert parametros_update["usuario_id"] == 2
    assert parametros_update["nombre"] == "Estudiante actualizado"
