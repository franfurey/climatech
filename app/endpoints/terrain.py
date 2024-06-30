# app/endpoints/terrain.py
import json
from sqlalchemy import func
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.models.place import Place
from app.database.database import get_db

router = APIRouter()

@router.get("/{place_id}", response_class=JSONResponse)
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

def calculate_bounds(geojson_data: str):
    geojson = json.loads(geojson_data)
    coordinates = geojson['coordinates'][0]
    lats = [coord[1] for coord in coordinates]
    lngs = [coord[0] for coord in coordinates]
    return [[min(lats), min(lngs)], [max(lats), max(lngs)]]
