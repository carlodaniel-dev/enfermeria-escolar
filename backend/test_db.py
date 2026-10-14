
from sqlalchemy import text

from app.db.session import engine


def verificar_tablas():
    consulta = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)

    with engine.connect() as connection:
        tablas = connection.execute(consulta).scalars().all()

    print("Tablas encontradas en PostgreSQL:")
    for tabla in tablas:
        print(f"- {tabla}")

    print(f"\nTotal de tablas: {len(tablas)}")


if __name__ == "__main__":
    verificar_tablas()
