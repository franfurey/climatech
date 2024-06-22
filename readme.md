## Comandos Clave
- **Generar estructura del proyecto**:
  ```bash
  tree --prune -I 'venv|__pycache__|*.pyc|*.pyo|*.log|*.db|*.sqlite|*.egg-info|__init__.py' > estructura_proyecto.txt
  ```
- **Levantar Servidor**:
  ```
  uvicorn app.main:app --reload
  ```

# Descripción General del Proyecto
Proyecto de aplicación web desarrollada con FastAPI para visualizar y gestionar lugares geoespaciales. Utiliza PostgreSQL con PostGIS para la manipulación de datos geográficos, y ofrece funcionalidades para añadir, visualizar y eliminar lugares.

## Componentes del Sistema
Backend: FastAPI
Base de Datos: PostgreSQL con PostGIS
Frontend: Jinja2 para renderizado de plantillas, Leaflet para mapas interactivos

## Documentación de Endpoints
Root Endpoint
GET /: Retorna HTML con la lista de todos los lugares.
Detalles del Terreno
GET /terrain/{place_id}: Retorna datos GeoJSON del lugar especificado por ID.
Visualización de Mapas
GET /map/{place_id}: Muestra el mapa interactivo de un lugar específico.
Añadir un Nuevo Lugar
POST /add_place: Añade un lugar nuevo al sistema y redirige a la página principal.
Eliminación de Lugares
DELETE /delete_place/{place_id}: Elimina un lugar por su ID y cualquier archivo GeoJSON asociado.
Información del Producto
GET /get_product/{product_id}: Muestra información de un producto utilizando la API APPEARS.

## Estructura de Directorios
  ```
.
├── alembic
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       ├── 01bb1e17a192_initial_migration.py
│       └── 300038457dbc_initial_migration.py
├── alembic.ini
├── app
│   ├── create_tables.py
│   ├── database.py
│   ├── external_apis
│   │   └── appears
│   │       ├── appears.py
│   │       └── auth.py
│   ├── main.py
│   ├── models.py
│   ├── static
│   │   ├── Campo Nonos.geojson
│   │   ├── La Calera - Cerro Piedra Relumbrosa.geojson
│   │   └── Santa Fe.geojson
│   └── templates
│       ├── base.html
│       ├── index.html
│       └── map.html
├── estructura_proyecto.txt
├── readme.md
├── requirements.txt
├── start.sh
└── test_asyncpg.py
  ```

8 directories, 23 files