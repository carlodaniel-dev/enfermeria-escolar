
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine
from app.schemas.atencion import AtencionActualizar, AtencionCrear


def crear_atencion(datos: AtencionCrear, usuario_id: int) -> dict:
    with engine.begin() as connection:
        estudiante = connection.execute(
            text("""
                SELECT id
                FROM public.estudiante
                WHERE id = :id
            """),
            {"id": datos.estudiante_id},
        ).first()

        if estudiante is None:
            raise ValueError("El estudiante seleccionado no existe.")

        usuario = connection.execute(
            text("""
                SELECT id
                FROM public.usuario
                WHERE id = :id
                    AND activo = TRUE
            """),
            {"id": usuario_id},
        ).first()

        if usuario is None:
            raise ValueError("El usuario no existe o está inactivo.")

        diagnostico = connection.execute(
            text("""
                SELECT nombre
                FROM public.diagnostico
                WHERE id = :id
                    AND activo = TRUE
            """),
            {"id": datos.diagnostico_id},
        ).mappings().first()

        if diagnostico is None:
            raise ValueError("El diagnóstico no existe o está inactivo.")

        descripcion = datos.descripcion_diagnostico
        if descripcion is not None:
            descripcion = descripcion.strip() or None

        if diagnostico["nombre"].strip().lower() == "otros":
            if not descripcion:
                raise ValueError(
                    "Debes describir el diagnóstico cuando seleccionas Otros."
                )
        elif descripcion:
            raise ValueError(
                "La descripción adicional solo se permite para el diagnóstico Otros."
            )

        fila = connection.execute(
            text("""
                INSERT INTO public.atencion (
                    estudiante_id,
                    saturacion,
                    frecuencia_cardiaca,
                    temperatura,
                    diagnostico_id,
                    descripcion_diagnostico,
                    recomendacion,
                    usuario_id
                )
                VALUES (
                    :estudiante_id,
                    :saturacion,
                    :frecuencia_cardiaca,
                    :temperatura,
                    :diagnostico_id,
                    :descripcion_diagnostico,
                    :recomendacion,
                    :usuario_id
                )
                RETURNING
                    id,
                    estudiante_id,
                    fecha_hora,
                    saturacion,
                    frecuencia_cardiaca,
                    temperatura,
                    diagnostico_id,
                    descripcion_diagnostico,
                    recomendacion,
                    usuario_id,
                    modificado_por,
                    fecha_modificacion
            """),
            {
                "estudiante_id": datos.estudiante_id,
                "saturacion": datos.saturacion,
                "frecuencia_cardiaca": datos.frecuencia_cardiaca,
                "temperatura": datos.temperatura,
                "diagnostico_id": datos.diagnostico_id,
                "descripcion_diagnostico": descripcion,
                "recomendacion": datos.recomendacion,
                "usuario_id": usuario_id,
            },
        ).mappings().one()

        return dict(fila)



def obtener_atenciones() -> list[dict]:
    consulta = text("""
        SELECT
            a.id,
            a.estudiante_id,
            e.nombre AS estudiante,
            c.nombre AS curso,
            c.nivel,
            p.nombre AS paralelo,
            es.nombre AS especialidad,
            a.fecha_hora,
            a.saturacion,
            a.frecuencia_cardiaca,
            a.temperatura,
            a.diagnostico_id,
            d.nombre AS diagnostico,
            a.descripcion_diagnostico,
            a.recomendacion,
            a.usuario_id,
            u.nombre AS usuario,
            a.modificado_por,
            a.fecha_modificacion
        FROM public.atencion AS a
        INNER JOIN public.estudiante AS e
            ON e.id = a.estudiante_id
        INNER JOIN public.curso AS c
            ON c.id = e.curso_id
        LEFT JOIN public.paralelo AS p
            ON p.id = e.paralelo_id
        LEFT JOIN public.especialidad AS es
            ON es.id = e.especialidad_id
        INNER JOIN public.diagnostico AS d
            ON d.id = a.diagnostico_id
        INNER JOIN public.usuario AS u
            ON u.id = a.usuario_id
        ORDER BY a.fecha_hora DESC, a.id DESC
    """)

    with engine.connect() as connection:
        filas = connection.execute(consulta).mappings().all()
        return [dict(fila) for fila in filas]


def actualizar_atencion(
    atencion_id: int,
    datos: AtencionActualizar,
    usuario_actual: dict,
) -> dict:
    with engine.begin() as connection:
        atencion = connection.execute(
            text("""
                SELECT id, usuario_id
                FROM public.atencion
                WHERE id = :id
                FOR UPDATE
            """),
            {"id": atencion_id},
        ).mappings().first()

        if atencion is None:
            raise LookupError("La atención no existe.")

        es_admin = usuario_actual["rol"] == "Admin"
        es_creador = atencion["usuario_id"] == usuario_actual["id"]

        if not es_admin and not es_creador:
            raise PermissionError(
                "Solo puedes modificar tus propias atenciones."
            )

        diagnostico = connection.execute(
            text("""
                SELECT nombre
                FROM public.diagnostico
                WHERE id = :id
                    AND activo = TRUE
            """),
            {"id": datos.diagnostico_id},
        ).mappings().first()

        if diagnostico is None:
            raise ValueError("El diagnóstico no existe o está inactivo.")

        descripcion = datos.descripcion_diagnostico
        if descripcion is not None:
            descripcion = descripcion.strip() or None

        if diagnostico["nombre"].strip().lower() == "otros":
            if not descripcion:
                raise ValueError(
                    "Debes describir el diagnóstico cuando seleccionas Otros."
                )
        elif descripcion:
            raise ValueError(
                "La descripción adicional solo se permite para el diagnóstico Otros."
            )

        fila = connection.execute(
            text("""
                UPDATE public.atencion
                SET
                    saturacion = :saturacion,
                    frecuencia_cardiaca = :frecuencia_cardiaca,
                    temperatura = :temperatura,
                    diagnostico_id = :diagnostico_id,
                    descripcion_diagnostico = :descripcion_diagnostico,
                    recomendacion = :recomendacion,
                    modificado_por = :modificado_por
                WHERE id = :id
                RETURNING
                    id,
                    estudiante_id,
                    fecha_hora,
                    saturacion,
                    frecuencia_cardiaca,
                    temperatura,
                    diagnostico_id,
                    descripcion_diagnostico,
                    recomendacion,
                    usuario_id,
                    modificado_por,
                    fecha_modificacion
            """),
            {
                "id": atencion_id,
                "saturacion": datos.saturacion,
                "frecuencia_cardiaca": datos.frecuencia_cardiaca,
                "temperatura": datos.temperatura,
                "diagnostico_id": datos.diagnostico_id,
                "descripcion_diagnostico": descripcion,
                "recomendacion": datos.recomendacion,
                "modificado_por": usuario_actual["id"],
            },
        ).mappings().one()

        return dict(fila)
