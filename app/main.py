# app/main.py

import os
import json
from sqlalchemy import func
from shapely.geometry import shape
from sqlalchemy.future import select
from geoalchemy2.shape import from_shape
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi import FastAPI, Depends, HTTPException, Request, Form, File, UploadFile

from .models import Place
from .database import get_db

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
    result = await db.execute(
        select(
            Place.id, 
            Place.name, 
            Place.description,
            func.ST_AsGeoJSON(Place.location).label('geojson')
        ).where(Place.id == place_id)
    )
    place_data = result.fetchone()  # Cambio aquí para obtener la primera fila de los resultados
    if not place_data:
        raise HTTPException(status_code=404, detail="Place not found")

    # Usar indexación si los resultados son tratados como una tupla
    geojson_data = json.loads(place_data.geojson)  # Acceso correcto al campo geojson

    if 'coordinates' in geojson_data:
        coordinates = geojson_data['coordinates'][0]
        lats = [coord[1] for coord in coordinates]
        lngs = [coord[0] for coord in coordinates]
        bounds = [[min(lats), min(lngs)], [max(lats), max(lngs)]]
    else:
        raise HTTPException(status_code=500, detail="Invalid GeoJSON data")
    
    return {"geojson": geojson_data, "bounds": bounds}


@app.get("/map/{place_id}", response_class=HTMLResponse)
async def show_map(request: Request, place_id: int, db: AsyncSession = Depends(get_db)):
    place = await db.get(Place, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    template = env.get_template("map.html")
    return HTMLResponse(template.render(request=request, place_id=place_id))

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

from external_apis.appears.auth import get_appears_token
from external_apis.appears.appears import get_product_info

@app.route('/get_product/<product_id>')
async def show_product_info(product_id):
    token = get_appears_token('your_username', 'your_password')  # Guardar estos valores de forma segura
    product_info = get_product_info(token, product_id)
    return product_info
