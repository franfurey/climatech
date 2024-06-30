# app/create_tables.py
import asyncio
import psycopg2
import psycopg2.errors
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from app.models import HarmonizedLandsatSentinelData, Place, Base

DATABASE_SERVER_URL = "postgresql://franciscofurey@localhost/"
DATABASE_NAME = "climatech"

def create_database():
    # Conexión directa al servidor PostgreSQL sin especificar base de datos
    conn = psycopg2.connect(DATABASE_SERVER_URL)
    conn.autocommit = True  # Importante para ejecutar CREATE DATABASE y CREATE EXTENSION fuera de transacción
    cur = conn.cursor()
    try:
        # Intenta crear la base de datos
        cur.execute(f"CREATE DATABASE {DATABASE_NAME}")
        print(f"Database '{DATABASE_NAME}' created successfully.")
    except psycopg2.errors.DuplicateDatabase:
        print(f"Database '{DATABASE_NAME}' already exists.")
    
    # Cierra la conexión a la base de datos
    cur.close()
    conn.close()

    # Conexión a la nueva base de datos para instalar PostGIS
    conn = psycopg2.connect(f"{DATABASE_SERVER_URL}{DATABASE_NAME}")
    conn.autocommit = True
    cur = conn.cursor()
    try:
        # Instala PostGIS
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        print("PostGIS extension created successfully.")
    except Exception as e:
        print(f"An error occurred while creating PostGIS extension: {str(e)}")
    finally:
        cur.close()
        conn.close()

async def create_tables():
    # Conexión a la base de datos específica utilizando async SQLAlchemy
    engine = create_async_engine(f"postgresql+asyncpg://franciscofurey@localhost/{DATABASE_NAME}", echo=True)
    async with engine.begin() as conn:
        # Crea todas las tablas definidas en Base
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")
    await engine.dispose()

if __name__ == "__main__":
    # Ejecuta la creación de la base de datos y luego crea las tablas
    create_database()
    asyncio.run(create_tables())
