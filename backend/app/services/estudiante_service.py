
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine
from app.schemas.estudiante import EstudianteCrear


def obtener_estudiantes() -> list[dict]:
    consulta = text("""
        SELECT
            e.id,
            e.nombre,
            e.curso_id,
            c.nombre AS curso,
            c.nivel,
            e.paralelo_id,
            p.nombre AS paralelo,
            e.especialidad_id,
            es.nombre AS especialidad,
            e.sexo
        FROM public.estudiante AS e
        INNER JOIN public.curso AS c
            ON c.id = e.curso_id
        LEFT JOIN public.paralelo AS p
            ON p.id = e.paralelo_id
        LEFT JOIN public.especialidad AS es
            ON es.id = e.especialidad_id
        ORDER BY e.id
    """)

    with engine.connect() as connection:
        filas = connection.execute(consulta).mappings().all()
        return [dict(fila) for fila in filas]


def crear_estudiante(datos: EstudianteCrear) -> dict:
    nombre = datos.nombre.strip()

    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    with engine.begin() as connection:
        curso = connection.execute(
            text("""
                SELECT nivel
                FROM public.curso
                WHERE id = :curso_id
            """),
            {"curso_id": datos.curso_id},
        ).mappings().first()

        if curso is None:
            raise ValueError("El curso seleccionado no existe.")

        if curso["nivel"] == "Bachillerato":
            if datos.especialidad_id is None:
                raise ValueError(
                    "Bachillerato requiere una especialidad."
                )
            if datos.paralelo_id is not None:
                raise ValueError(
                    "Bachillerato no debe tener paralelo."
                )
        else:
            if datos.paralelo_id is None:
                raise ValueError(
                    "Inicial y EGB requieren un paralelo."
                )
            if datos.especialidad_id is not None:
                raise ValueError(
                    "Inicial y EGB no deben tener especialidad."
                )

        if datos.paralelo_id is not None:
            existe = connection.execute(
                text("""
                    SELECT 1
                    FROM public.paralelo
                    WHERE id = :id
                """),
                {"id": datos.paralelo_id},
            ).first()

            if existe is None:
                raise ValueError("El paralelo seleccionado no existe.")

        if datos.especialidad_id is not None:
            existe = connection.execute(
                text("""
                    SELECT 1
                    FROM public.especialidad
                    WHERE id = :id
                """),
                {"id": datos.especialidad_id},
            ).first()

            if existe is None:
                raise ValueError(
                    "La especialidad seleccionada no existe."
                )

        nuevo = connection.execute(
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
                RETURNING id
            """),
            {
                "nombre": nombre,
                "curso_id": datos.curso_id,
                "paralelo_id": datos.paralelo_id,
                "especialidad_id": datos.especialidad_id,
                "sexo": datos.sexo,
            },
        ).mappings().one()

        estudiante_id = nuevo["id"]

        resultado = connection.execute(
            text("""
                SELECT
                    e.id,
                    e.nombre,
                    e.curso_id,
                    c.nombre AS curso,
                    c.nivel,
                    e.paralelo_id,
                    p.nombre AS paralelo,
                    e.especialidad_id,
                    es.nombre AS especialidad,
                    e.sexo
                FROM public.estudiante AS e
                INNER JOIN public.curso AS c
                    ON c.id = e.curso_id
                LEFT JOIN public.paralelo AS p
                    ON p.id = e.paralelo_id
                LEFT JOIN public.especialidad AS es
                    ON es.id = e.especialidad_id
                WHERE e.id = :id
            """),
            {"id": estudiante_id},
        ).mappings().one()

        return dict(resultado)
