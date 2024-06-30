# app/endpoints/ndvi.py
import os
import asyncio
from sqlalchemy.future import select
from sqlalchemy import func, distinct
from geoalchemy2.shape import to_shape
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_db
from app.config.log_config import logger
from app.models import HarmonizedLandsatSentinelData
from app.external_apis.appears.auth import get_appears_token
from app.external_apis.appears.harmonized_landsat_sentinel_data import fetch_and_store_hls_data, \
    check_task_status, list_task_files, download_and_process_file

router = APIRouter()

@router.get("/{place_id}")
async def get_ndvi(place_id: int, db: AsyncSession = Depends(get_db)):
    current_time = datetime.now()
    one_month_ago = current_time - timedelta(days=30)

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

@router.get("/dates/{place_id}")
async def get_ndvi_dates(place_id: int, db: AsyncSession = Depends(get_db)):
    dates_query = select(distinct(HarmonizedLandsatSentinelData.capture_date)).where(HarmonizedLandsatSentinelData.place_id == place_id)
    result = await db.execute(dates_query)
    dates = [record[0] for record in result.fetchall()]
    return {"dates": dates}

@router.get("/heatmap/{place_id}")
async def get_ndvi_heatmap(place_id: int, date: str = None, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received request for place_id: {place_id} with date: {date}")
    if date:
        try:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
            logger.info(f"Parsed date object: {date_obj}")
        except ValueError as e:
            logger.error(f"Error parsing date: {date}, Error: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS.sss.")
        condition = (HarmonizedLandsatSentinelData.capture_date == date_obj)
    else:
        condition = None

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
