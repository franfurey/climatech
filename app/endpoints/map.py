# app/endpoints/map.py
from sqlalchemy.future import select
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import Place
from app.database.database import get_db
from app.config.log_config import logger

router = APIRouter()

env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(['html', 'xml'])
)

@router.get("/{place_id}", response_class=HTMLResponse)
async def show_map(request: Request, place_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Fetching place with ID: {place_id}")
    statement = select(Place).where(Place.id == place_id)
    result = await db.execute(statement)
    place = result.scalars().first()

    if not place:
        logger.error(f"Place not found with ID: {place_id}")
        raise HTTPException(status_code=404, detail="Place not found")

    logger.info(f"Place found: {place.name} with ID: {place.id}")
    template = env.get_template("map.html")
    response = HTMLResponse(template.render(request=request, place=place))
    return response
