# app/endpoints/places.py
import json
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from shapely.geometry import shape
from sqlalchemy.future import select
from geoalchemy2.shape import from_shape
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File

from app.models.place import Place
from app.database.database import get_db
from app.config.log_config import logger

router = APIRouter()

class PlaceSchema(BaseModel):
    id: int
    name: str
    description: str
    location: Optional[str]  # A string is expected to be GeoJSON

    class Config:
        orm_mode = True

@router.get("/get_places", response_model=List[PlaceSchema])
async def get_places(db: AsyncSession = Depends(get_db)):
    async with db:
        result = await db.execute(select(Place.id, Place.name, Place.description, func.ST_AsGeoJSON(Place.location).label('location')))
        places = result.fetchall()
        return [{"id": place.id, "name": place.name, "description": place.description, "location": place.location} for place in places]

@router.post("/add_place")
async def add_place(name: str = Form(...), 
                    description: str = Form(...), 
                    geojson: UploadFile = File(...), 
                    db: AsyncSession = Depends(get_db)):
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

@router.delete("/delete_place/{place_id}")
async def delete_place(place_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting place: {place_id}")
    async with db as session:
        place = await session.get(Place, place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        try:
            logger.info(f"Attempting to delete place with ID: {place.id}")
            await session.delete(place)
            await session.commit()
            logger.info(f"Place with ID: {place.id} deleted successfully.")
            return {"message": "Place deleted successfully"}
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Failed to delete place with ID {place_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
