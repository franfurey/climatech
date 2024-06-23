# app/main.py
import os
import json
import asyncio
from sqlalchemy import func
from dotenv import load_dotenv
from shapely.geometry import shape
from sqlalchemy.future import select
from geoalchemy2.shape import from_shape
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi import FastAPI, Depends, HTTPException, Request, Form, File, UploadFile

from app.config.log_config import logger
from app.models import Place
from app.database import get_db
from app.external_apis.appears.appears import get_product_info
from app.external_apis.appears.auth import get_appears_token, get_aws_credentials
from app.external_apis.appears.harmonized_landsat_sentinel_data import fetch_and_store_hls_data, \
    check_task_status, list_task_files, download_and_process_file

# Load the environment variables from the .env file
load_dotenv()
 
app = FastAPI()

# Configura el entorno de Jinja2 directamente
env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(['html', 'xml'])
)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Place))
    places = result.scalars().all()
    template = env.get_template("index.html")
    return HTMLResponse(template.render(request=request, places=places))

@app.get("/terrain/{place_id}", response_class=JSONResponse)
async def get_terrain(place_id: int, db: AsyncSession = Depends(get_db)):
    print(f"Received place_id: {place_id}")  # Imprime el place_id recibido
    result = await db.execute(
        select(
            Place.id, 
            Place.name, 
            Place.description,
            func.ST_AsGeoJSON(Place.location).label('geojson')
        ).where(Place.id == place_id)
    )
    place_data = result.fetchone()
    if not place_data:
        print("Place not found")  # Mensaje si no se encuentra el lugar
        raise HTTPException(status_code=404, detail="Place not found")

    print(f"Place data: {place_data}")  # Imprime los datos del lugar
    return {"geojson": json.loads(place_data.geojson), "bounds": calculate_bounds(place_data.geojson)}

def calculate_bounds(geojson_data):
    geojson = json.loads(geojson_data)
    coordinates = geojson['coordinates'][0]
    lats = [coord[1] for coord in coordinates]
    lngs = [coord[0] for coord in coordinates]
    return [[min(lats), min(lngs)], [max(lats), max(lngs)]]

@app.get("/map/{place_id}", response_class=HTMLResponse)
async def show_map(request: Request, place_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Fetching place with ID: {place_id}")
    statement = select(Place).where(Place.id == place_id)
    result = await db.execute(statement)
    place = result.scalars().first()

    if not place:
        logger.error(f"Place not found with ID: {place_id}")
        raise HTTPException(status_code=404, detail="Place not found")

    logger.info(f"Place found: {place.name} with ID: {place.id}")
    # Pasa el objeto place completo a la plantilla
    template = env.get_template("map.html")
    response = HTMLResponse(template.render(request=request, place=place))
    logger.info(f"Rendering map for place ID {place_id}")
    return response

@app.post("/add_place")
async def add_place(name: str = Form(...), description: str = Form(...), geojson: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    geojson_data = json.loads(await geojson.read())
    shapely_geometry = shape(geojson_data['features'][0]['geometry'])
    new_place = Place(name=name, description=description, location=from_shape(shapely_geometry, srid=4326))
    db.add(new_place)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Place already exists")

    return RedirectResponse(url="/", status_code=303)

@app.delete("/delete_place/{place_id}")
async def delete_place(place_id: int, db: AsyncSession = Depends(get_db)):
    place = await db.get(Place, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    file_path = os.path.join("app", place.geojson_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    await db.delete(place)
    await db.commit()

    return {"message": "Place deleted successfully"}

@app.route('/get_product/<product_id>')
async def show_product_info(product_id: int):
    # Acceder a las variables de entorno
    user = os.getenv("APPEARS_USER")
    password = os.getenv("APPEARS_PASS")

    if not user or not password:
        return {"error": "API credentials are not available"}

    token = get_appears_token(username=user, password=password)
    product_info = get_product_info(token, product_id)
    return product_info

@app.get("/ndvi/{place_id}")
async def get_ndvi(place_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Iniciando la recuperación de datos para el lugar ID: {place_id}")

    # Obtén el token de APPEARS
    token = get_appears_token(username=os.getenv("APPEARS_USER"), password=os.getenv("APPEARS_PASS"))

    response = await fetch_and_store_hls_data(place_id=place_id, db=db, token=token)
    if response.get("error"):
        logger.error(f"Error al iniciar la recuperación de datos: {response['error']}")
        raise HTTPException(status_code=400, detail=response["error"])

    task_id = response.get("task_id")
    logger.info(f"Tarea enviada con ID: {task_id}, esperando a que finalice")
    while not await check_task_status(task_id=task_id, token=token):
        logger.info("Tarea no completada, esperando otro minuto...")
        await asyncio.sleep(60)

    logger.info("Tarea completada, procediendo a descargar y procesar archivos")
    files = await list_task_files(task_id=task_id, token=token)

    # Procesa archivos usando la API de AppEEARS
    for file_info in files:
        file_id = file_info['file_id']
        file_name = file_info['file_name']
        logger.info(f"Procesando archivo: {file_name} con ID: {file_id}")
        await download_and_process_file(task_id=task_id, 
                                        file_id=file_id, 
                                        file_name=file_name, 
                                        place_id=place_id, 
                                        db=db, 
                                        token=token)

    logger.info("Todos los archivos han sido procesados exitosamente")
    return {"message": "All files processed successfully"}