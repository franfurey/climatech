# app/router.py
from fastapi import APIRouter
from app.endpoints import places, terrain, map, ndvi, wild_fires

router = APIRouter()
router.include_router(places.router, prefix="/places", tags=["Places"])
router.include_router(terrain.router, prefix="/terrain", tags=["Terrain"])
router.include_router(map.router, prefix="/map", tags=["Map"])
router.include_router(ndvi.router, prefix="/ndvi", tags=["NDVI"])
router.include_router(wild_fires.router, tags=["Wildfires"])