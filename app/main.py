# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
import os

from .database import get_db
from .models import Place, Base

app = FastAPI()

# Configura el entorno de Jinja2 directamente
env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(['html', 'xml'])
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Place))
    places = result.scalars().all()
    template = env.get_template("index.html")
    return HTMLResponse(template.render(request=request, places=places))

@app.get("/terrain/{place_id}", response_class=JSONResponse)
async def get_terrain(place_id: int, db: AsyncSession = Depends(get_db)):
    place = await db.get(Place, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    file_path = os.path.join("app", place.geojson_path)
    with open(file_path, 'r') as f:
        geojson_data = json.load(f)

    coords = geojson_data["features"][0]["geometry"]["coordinates"][0]
    lats = [coord[1] for coord in coords]
    lngs = [coord[0] for coord in coords]
    bounds = [[min(lats), min(lngs)], [max(lats), max(lngs)]]

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
    geojson_path = f"static/{name}.geojson"
    
    file_location = os.path.join("app", geojson_path)
    with open(file_location, "wb") as file:
        file.write(await geojson.read())
    
    new_place = Place(name=name, description=description, geojson_path=geojson_path)
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