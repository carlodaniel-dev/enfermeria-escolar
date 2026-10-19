
from sqlalchemy import text

from app.db.session import engine
from app.schemas.estudiante import EstudianteActualizar, EstudianteCrear


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
                raise ValueError(
                    "El paralelo seleccionado no existe."
                )

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


def actualizar_estudiante(
    estudiante_id: int,
    datos: EstudianteActualizar,
    usuario_id: int,
) -> dict:
    nombre = datos.nombre.strip()

    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    with engine.begin() as connection:
        # Verificar primero que el estudiante exista.
        estudiante_existente = connection.execute(
            text("""
                SELECT 1
                FROM public.estudiante
                WHERE id = :estudiante_id
            """),
            {"estudiante_id": estudiante_id},
        ).first()

        if estudiante_existente is None:
            raise LookupError("El estudiante no existe.")

        # Validar el curso seleccionado.
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

        # Validar los requisitos académicos según el nivel.
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

        # Verificar que el paralelo exista, cuando corresponda.
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
                raise ValueError(
                    "El paralelo seleccionado no existe."
                )

        # Verificar que la especialidad exista, cuando corresponda.
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

        # Actualizar los datos y registrar quién realizó el cambio.
        actualizado = connection.execute(
            text("""
                UPDATE public.estudiante
                SET nombre = :nombre,
                    curso_id = :curso_id,
                    paralelo_id = :paralelo_id,
                    especialidad_id = :especialidad_id,
                    sexo = :sexo,
                    modificado_por = :usuario_id
                WHERE id = :estudiante_id
                RETURNING id
            """),
            {
                "estudiante_id": estudiante_id,
                "nombre": nombre,
                "curso_id": datos.curso_id,
                "paralelo_id": datos.paralelo_id,
                "especialidad_id": datos.especialidad_id,
                "sexo": datos.sexo,
                "usuario_id": usuario_id,
            },
        ).mappings().first()

        # Protección adicional ante una actualización sin resultado.
        if actualizado is None:
            raise LookupError("El estudiante no existe.")

        # Devolver los datos actualizados y la auditoría.
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
                    e.sexo,
                    e.modificado_por,
                    e.fecha_modificacion
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


def obtener_auditoria_estudiante(estudiante_id: int) -> dict:
    with engine.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT
                    e.id AS estudiante_id,
                    e.nombre AS estudiante,
                    e.modificado_por,
                    u.nombre AS modificado_por_nombre,
                    u.email AS modificado_por_email,
                    e.fecha_modificacion
                FROM public.estudiante AS e
                LEFT JOIN public.usuario AS u
                    ON u.id = e.modificado_por
                WHERE e.id = :estudiante_id
            """),
            {"estudiante_id": estudiante_id},
        ).mappings().first()

        if resultado is None:
            raise LookupError("El estudiante no existe.")

        return dict(resultado)
