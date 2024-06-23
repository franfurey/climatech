## Key Commands
- **Generate project structure**:
  ```bash
  tree --prune -I 'venv|__pycache__|*.pyc|*.pyo|*.log|*.db|*.sqlite|*.egg-info|__init__.py' > project_structure.txt
  ```
- **Lift Server**:
  ```
  uvicorn app.main:app --reload
  ```

# General Description of the Project
Web application project developed with FastAPI to visualize and manage geospatial places. It uses PostgreSQL with PostGIS for geographic data manipulation, and offers functionalities for adding, viewing and deleting places.

## System Components
Backend: FastAPI
Database: PostgreSQL with PostGIS
Frontend: Jinja2 for template rendering, Leaflet for interactive mapping

## Endpoint Documentation
- **Root Endpoint**:
GET /: Return HTML with list of all locations.
- **Terrain Details**:
GET /terrain/{place_id}: Returns GeoJSON data of the place specified by ID.
- **Map Display**:
GET /map/{place_id}: Displays the interactive map of a specified place.
- **Add a New Place**:
POST /add_place: Adds a new place to the system and redirects to the main page.
- **Deleting Places**:
DELETE /delete_place/{place_id}: Deletes a place by its ID and any associated GeoJSON file.
- **Product Information**:
GET /get_product/{product_id}: Displays information about a product using the APPEARS API.

## Directory Structure
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