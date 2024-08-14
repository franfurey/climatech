## Key Commands
- **Generate project structure**:
  ```bash
  tree --prune -I 'venv|__pycache__|*.pyc|*.pyo|*.log|*.db|*.sqlite|*.egg-info|__init__.py|node_modules|build|*.js.map|*.css.map' > project_structure.txt
  ```
- **Lift Backend Server**:
  ```
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
- **Lift Frontend Server**:
  ```
  cd frontend
  ```
  ```
  npm start
  ```

# README for FastAPI Geospatial Web Application

This document serves as a comprehensive guide for understanding the structure and functionality of the FastAPI web application designed for managing geospatial data. It is intended for use with Language Models (LLMs) to facilitate a quick and easy grasp of the project's components. The application leverages PostgreSQL with PostGIS for geographic data storage and manipulation, and uses Alembic for database schema migrations, ensuring that database versions are managed and tracked consistently.

# General Description of the Project
Web application project developed with FastAPI to visualize and manage geospatial places. It uses PostgreSQL with PostGIS for geographic data manipulation, and offers functionalities for adding, viewing and deleting places.

## System Components
Backend: FastAPI
Database: PostgreSQL with PostGIS
Frontend: React

## Endpoint Documentation

### Places
- **Get Places**:
  - **Endpoint**: `GET /places/get_places`
  - **Description**: Retrieves a list of all places in the system.

- **Add Place**:
  - **Endpoint**: `POST /places/add_place`
  - **Description**: Adds a new place to the system and redirects to the main page.

- **Delete Place**:
  - **Endpoint**: `DELETE /places/delete_place/{place_id}`
  - **Description**: Deletes a place by its ID and any associated GeoJSON file.

### Terrain
- **Get Terrain**:
  - **Endpoint**: `GET /terrain/{place_id}`
  - **Description**: Returns GeoJSON data of the place specified by ID.

### Map
- **Show Map**:
  - **Endpoint**: `GET /map/{place_id}`
  - **Description**: Displays the interactive map of a specified place.

### NDVI
- **Get NDVI**:
  - **Endpoint**: `GET /ndvi/{place_id}`
  - **Description**: Retrieves normalized difference vegetation index (NDVI) data for a specified place. This endpoint initiates an asynchronous task to fetch and process satellite imagery data, converting it into NDVI measurements.
  - **Details**:
    - **Parameters**:
      - `place_id`: Integer, ID of the place for which NDVI data is requested.
    - **Returns**: On successful execution, returns a message indicating all files have been processed successfully. If an error occurs during data retrieval or processing, it responds with an appropriate error message and status code.
    - **Flow**:
      - Validates the existence of the specified place.
      - Fetches satellite data for the last 30 days from the AppEEARS API using the given credentials.
      - Processes the data to compute NDVI values.
      - Stores the processed data in the database.
      - Continuously checks the task status until completion and handles the data accordingly.

- **Get NDVI Dates**:
  - **Endpoint**: `GET /ndvi/dates/{place_id}`
  - **Description**: Retrieves available dates for NDVI data for a specified place.
  - **Details**:
    - **Parameters**:
      - `place_id`: Integer, ID of the place for which NDVI dates are requested.
    - **Returns**: A list of dates for which NDVI data is available.

- **Get NDVI Heatmap**:
  - **Endpoint**: `GET /ndvi/heatmap/{place_id}`
  - **Description**: Retrieves NDVI heatmap data for a specified place and date.
  - **Details**:
    - **Parameters**:
      - `place_id`: Integer, ID of the place for which NDVI heatmap data is requested.
      - `date`: String (optional), specific date for the NDVI data in the format `YYYY-MM-DDTHH:MM:SS` or `YYYY-MM-DDTHH:MM:SS.sss`.
    - **Returns**: A heatmap of NDVI values for the specified place and date.


## Directory Structure
  ```
.
├── alembic
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       ├── 0c200b07e4b2_add_ndvi_column.py
│       └── cc4ed6cc1407_initial_migration.py
├── alembic.ini
├── app
│   ├── config
│   │   └── log_config.py
│   ├── database
│   │   ├── create_tables.py
│   │   └── database.py
│   ├── endpoints
│   │   ├── map.py
│   │   ├── ndvi.py
│   │   ├── places.py
│   │   └── terrain.py
│   ├── external_apis
│   │   └── appears
│   │       ├── appears.py
│   │       ├── auth.py
│   │       ├── harmonized_landsat_sentinel_data.py
│   │       └── utils_appears.py
│   ├── main.py
│   ├── models
│   │   ├── base.py
│   │   ├── harmonized_landsat_sentinel_data.py
│   │   └── place.py
│   └── router.py
├── frontend
│   ├── package-lock.json
│   ├── package.json
│   ├── public
│   │   ├── index.html
│   │   └── robots.txt
│   └── src
│       ├── App.css
│       ├── App.js
│       ├── BaseLayout.js
│       ├── components
│       │   ├── AddPlaceModal.js
│       │   ├── MapComponent.js
│       │   ├── PlacesList.js
│       │   ├── Sidebar.js
│       │   └── WildFiresMap.js
│       ├── index.css
│       ├── index.js
│       ├── reportWebVitals.js
│       └── styles.css
├── project_structure.txt
├── readme.md
├── requirements.txt
└── sandbox
    ├── database.ipynb
    ├── delete_all_tasks_appears.ipynb
    ├── firms
    │   ├── firms_api_use.ipynb
    │   ├── firms_data_ingest.ipynb
    │   └── firms_visualization.ipynb
    └── fran.ipynb

16 directories, 47 files
  ```