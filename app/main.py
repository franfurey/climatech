# app/main.py
import os
import json
import asyncio
from typing import List, Optional  
from sqlalchemy import func
from dotenv import load_dotenv
from shapely.geometry import shape
from sqlalchemy.future import select
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi import FastAPI, Depends, HTTPException, Request, Form, File, UploadFile

from app.database import get_db
from app.config.log_config import logger
from app.models import Place, HarmonizedLandsatSentinelData
from app.external_apis.appears.auth import get_appears_token
from app.external_apis.appears.appears import get_product_info
from app.external_apis.appears.harmonized_landsat_sentinel_data import fetch_and_store_hls_data, \
    check_task_status, list_task_files, download_and_process_file, calculate_ndvi_for_place

# Load the environment variables from the .env file
load_dotenv()
 
app = FastAPI()

# Configure the Jinja2 environment directly
env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(['html', 'xml'])
)

from pydantic import BaseModel
from typing import Optional

class PlaceSchema(BaseModel):
    id: int
    name: str
    description: str
    location: Optional[str]  # Se espera un string que sea GeoJSON

    class Config:
        orm_mode = True

@app.get("/api/places", response_model=List[PlaceSchema])
async def get_places(db: AsyncSession = Depends(get_db)):
    async with db:
        result = await db.execute(select(Place.id, Place.name, Place.description, func.ST_AsGeoJSON(Place.location).label('location')))
        places = result.fetchall()
        return [{"id": place.id, "name": place.name, "description": place.description, "location": place.location} for place in places]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Place))
    places = result.scalars().all()
    template = env.get_template("index.html")
    return HTMLResponse(template.render(request=request, places=places))

@app.get("/terrain/{place_id}", response_class=JSONResponse)
async def get_terrain(place_id: int, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=404, detail="Place not found")
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
    # Passes the complete place object to the template
    template = env.get_template("map.html")
    response = HTMLResponse(template.render(request=request, place=place))
    return response

@app.post("/add_place")
async def add_place(name: str = Form(...), 
                    description: str = Form(...), 
                    geojson: UploadFile = File(...), 
                    db: AsyncSession = Depends(get_db)
                    ):
    geojson_data = json.loads(await geojson.read())
    shapely_geometry = shape(geojson_data['features'][0]['geometry'])
    new_place = Place(name=name, description=description, location=from_shape(shapely_geometry, srid=4326))
    db.add(new_place)
    try:
        await db.commit()
        return {"message": "Place added successfully", "status": "success"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Place already exists")

from sqlalchemy.exc import SQLAlchemyError

@app.delete("/delete_place/{place_id}")
async def delete_place(place_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting place: {place_id}")
    async with db as session:
        place = await session.get(Place, place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        try:
            logger.info(f"Attempting to delete place with ID: {place.id}")
            await session.delete(place)  # Aquí debe ir el await
            await session.commit()  # Asegúrate de usar await aquí también
            logger.info(f"Place with ID: {place.id} deleted successfully.")
            return {"message": "Place deleted successfully"}
        except SQLAlchemyError as e:
            await session.rollback()  # Usa await aquí también
            logger.error(f"Failed to delete place with ID {place_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/ndvi/{place_id}")
async def get_ndvi(place_id: int, db: AsyncSession = Depends(get_db)):
    current_time = datetime.now()
    one_month_ago = current_time - timedelta(days=30)

    # Verify the existence of recent NDVI data
    most_recent_record = await db.execute(
        select(HarmonizedLandsatSentinelData)
        .where(
            HarmonizedLandsatSentinelData.place_id == place_id,
            HarmonizedLandsatSentinelData.capture_date > one_month_ago
        )
        .order_by(HarmonizedLandsatSentinelData.capture_date.desc())
    )
    most_recent_record = most_recent_record.scalars().first()

    if most_recent_record:
        logger.info("Recent NDVI data found in the database, avoiding new API request.")
        return JSONResponse(content={
            "message": "Recent NDVI data available"
        })

    # Processes the data if there are no recent
    token = get_appears_token(username=os.getenv("APPEARS_USER"), password=os.getenv("APPEARS_PASS"))
    response = await fetch_and_store_hls_data(place_id=place_id, db=db, token=token)
    if response.get("error"):
        logger.error(f"Error starting data recovery: {response['error']}")
        raise HTTPException(status_code=400, detail=response["error"])

    task_id = response.get("task_id")
    while not await check_task_status(task_id=task_id, token=token):
        await asyncio.sleep(60)

    files = await list_task_files(task_id=task_id, token=token)
    for file_info in files:
        await download_and_process_file(
            task_id=task_id,
            file_id=file_info['file_id'],
            file_name=file_info['file_name'],
            place_id=place_id,
            db=db,
            token=token
        )

    return JSONResponse(content={
        "message": "NDVI data processed and updated successfully"
    })

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from fastapi.responses import JSONResponse
from geoalchemy2.shape import to_shape
from sqlalchemy import distinct

@app.get("/ndvi/dates/{place_id}")
async def get_ndvi_dates(place_id: int, db: AsyncSession = Depends(get_db)):
    dates_query = select(distinct(HarmonizedLandsatSentinelData.capture_date)).where(HarmonizedLandsatSentinelData.place_id == place_id)
    result = await db.execute(dates_query)
    dates = [record[0] for record in result.fetchall()]
    return {"dates": dates}

@app.get("/ndvi/heatmap/{place_id}")
async def get_ndvi_heatmap(place_id: int, date: str = None, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received request for place_id: {place_id} with date: {date}")

    if date:
        try:
            try:
                # Primero intenta con milisegundos
                date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                # Si falla, intenta sin milisegundos
                date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
            logger.info(f"Parsed date object: {date_obj}")
        except ValueError as e:
            logger.error(f"Error parsing date: {date}, Error: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS.sss.")
        condition = (HarmonizedLandsatSentinelData.capture_date == date_obj)
    else:
        condition = None  # Añadir lógica para manejar la ausencia de fecha si es necesario

    try:
        ndvi_data_query = select(HarmonizedLandsatSentinelData).where(HarmonizedLandsatSentinelData.place_id == place_id, condition)
        result = await db.execute(ndvi_data_query)
        ndvi_records = result.scalars().all()
        logger.info(f"NDVI records fetched: {len(ndvi_records)}")
    except Exception as e:
        logger.error(f"Failed to fetch NDVI data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch data")

    if not ndvi_records:
        logger.warning("No NDVI data found for this place on the selected date")
        raise HTTPException(status_code=404, detail="No NDVI data found")

    heatmap_data = [
        {"latitude": to_shape(record.location).y, "longitude": to_shape(record.location).x, "ndvi": record.ndvi}
        for record in ndvi_records
    ]

    logger.info(f"Returning {len(heatmap_data)} records in the heatmap data")
    return {"data": heatmap_data}