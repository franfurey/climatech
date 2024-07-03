# app/endpoints/wild_fires.py
import requests
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends

from app.models import WildFireData
from app.config.log_config import logger
from app.database.database import get_db
import os

router = APIRouter()

@router.get("/wildfires")
async def get_wildfires(satellite: str, days: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Fetching wildfire data for satellite {satellite} over the past {days} days.")
    
    MAP_KEY = os.getenv("FIRMS_MAP_KEY")
    url = f'https://firms.modaps.eosdis.nasa.gov/api/country/csv/{MAP_KEY}/{satellite}/ARG/{days}'
    logger.info(f"Fetching data from FIRMS API: {url}")
    
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to fetch data: {response.status_code} {response.text}")
        raise HTTPException(status_code=400, detail="Error fetching wildfire data")

    logger.info("Data fetched successfully from external API.")
    data = response.text.splitlines()
    logger.info(f"Total number of lines received (including header): {len(data)}")
    logger.info("First 5 lines of data:")
    for line in data[:5]:
        logger.info(line)

    if len(data) > 1:
        # Asumiendo que la primera línea es el encabezado
        header = data[0].split(',')
        wildfires = [
            WildFireData(
                latitude=float(row.split(',')[header.index('latitude')]),
                longitude=float(row.split(',')[header.index('longitude')]),
                brightness=float(row.split(',')[header.index('brightness')]),
                scan=float(row.split(',')[header.index('scan')]),
                track=float(row.split(',')[header.index('track')]),
                acq_date=datetime.strptime(row.split(',')[header.index('acq_date')], '%Y-%m-%d'),
                acq_time=row.split(',')[header.index('acq_time')],
                satellite=row.split(',')[header.index('satellite')],
                confidence=row.split(',')[header.index('confidence')],
                version=row.split(',')[header.index('version')],
                bright_t31=float(row.split(',')[header.index('bright_t31')]),
                frp=float(row.split(',')[header.index('frp')]),
                daynight=row.split(',')[header.index('daynight')],
                location=f'POINT({row.split(',')[header.index('longitude')]} {row.split(',')[header.index('latitude')]})'
            ) for row in data[1:]  # Skip the header
        ]

        async with db.begin():
            db.add_all(wildfires)
            await db.commit()
    
    logger.info("Wildfire data committed to the database.")
    
    # Retrieving data from database to send back to client
    result = await db.execute(select(WildFireData))
    wildfires_data = result.scalars().all()
    logger.info(f"Retrieved {len(wildfires_data)} records from the database.")
    
    response_data = [{
        "id": wildfire.id,
        "latitude": wildfire.latitude,
        "longitude": wildfire.longitude,
        "brightness": wildfire.brightness,
        "acq_date": wildfire.acq_date.isoformat(),
        "acq_time": wildfire.acq_time,
        "satellite": wildfire.satellite,
        "confidence": wildfire.confidence
    } for wildfire in wildfires_data]

    logger.info("Sending data back to the client.")
    return response_data