# app/external_apis/appears/harmonized_landsat_sentinel_data.py
import re
import os
import json
import aiohttp
import requests
import rasterio
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.future import select
from shapely.geometry import mapping
from geoalchemy2.shape import to_shape
from datetime import datetime, timedelta
from geoalchemy2.elements import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.log_config import logger
from app.external_apis.appears.utils_appears import BAND_NAME_MAP
from app.models import Place, HarmonizedLandsatSentinelData

async def fetch_and_store_hls_data(place_id: int, 
                                   db: AsyncSession, 
                                   token
                                   ) -> dict:
    logger.info(f"Fetching place information for place_id: {place_id}")
    statement = select(Place).where(Place.id == place_id)
    result = await db.execute(statement)
    place = result.scalars().first()
    
    if not place:
        logger.error(f"No place found with place_id: {place_id}")
        return {"error": "Place not found"}

    end_date = datetime.now()
    start_date = end_date - timedelta(days=15)  # Two weeks earlier
    task_name = f"HarmonizedLandsatSentinelData-{end_date.strftime('%Y%m%d')}"

    logger.info(f"Submitting task for place_id {place_id} with task_name {task_name}")
    logger.info(f"Start date: {start_date.strftime('%m-%d-%Y')}, End date: {end_date.strftime('%m-%d-%Y')}")

    # Convert GeoAlchemy geometry to Shapely and create a FeatureCollection
    shapely_geom = to_shape(place.location)
    geo_json = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": mapping(shapely_geom),
                "properties": {}
            }
        ],
        "fileName": "User-Drawn-Polygon"  # Be sure to adjust this value if necessary.
    }
    logger.info(f"GeoJSON for place location: {json.dumps(geo_json)}")

    task_params = {
        "task_type": "area",
        "task_name": task_name,
        "params": {
            "geo": geo_json,
            "dates": [
                {"startDate": start_date.strftime("%m-%d-%Y"), "endDate": end_date.strftime("%m-%d-%Y")}
            ],
            "layers": [
                {"product": "HLSS30.020", "layer": layer} for layer in [
                    "B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B10", "B11", "B12", "B8A", 
                    "Fmask", "SAA", "SZA", "VAA", "VZA"
                ]
            ],
            "output": {
                "format": {"type": "geotiff"},
                "projection": "geographic",
                "additionalOptions": {}
            }
        }
    }

    logger.info(f"Task parameters: {json.dumps(task_params, indent=2)}")

    response = requests.post(
        "https://appeears.earthdatacloud.nasa.gov/api/task",
        headers={"Authorization": f"Bearer {token}"},
        json=task_params
    )

    if response.status_code == 202:
        task_response = response.json()
        task_id = task_response.get('task_id', None)
        if task_id:
            logger.info(f"Task submitted successfully with task_id: {task_id}")
            return {"message": "HLS data retrieval initiated successfully", "task_id": task_id}
        else:
            logger.warning("Task submitted but no task ID returned")
            return {"error": "Task submitted but no task ID returned", "status_code": response.status_code}
    else:
        logger.error(f"Failed to submit task: HTTP {response.status_code}")
        return {"error": "Failed to submit task", "status_code": response.status_code}

async def check_task_status(task_id: str, 
                            token: str
                            ) -> bool:
    """ Checks the status of the task and returns True if it is complete. """

    status_url = f"https://appeears.earthdatacloud.nasa.gov/api/task/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(status_url, headers=headers)
    if response.status_code == 200:
        task_info = response.json()
        task_status = task_info['status']
        logger.info(f"Task status {task_id}: {task_status}")
        return task_status == 'done'
    else:
        logger.error(f"Error checking task status {task_id}: HTTP {response.status_code}")
    return False

async def list_task_files(task_id: str, 
                          token: str
                          ) -> list:
    """ Lists the available files of a completed task. """

    url = f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = response.json()['files']
        logger.info(f"Files found for the task {task_id}: {len(files)} listed files")
        return files
    else:
        logger.warning(f"Could not list the files for the task {task_id}: HTTP {response.status_code}")
        return []

async def download_and_process_file(
                                    task_id: str, 
                                    file_id: str, 
                                    file_name: str, 
                                    place_id: int, 
                                    db: AsyncSession,
                                    token: str
                                    ):
    """Download and process a GeoTIFF file using AppEEARS API."""

    # Verify if the file is a GeoTIFF file
    if not file_name.endswith('.tif'):
        logger.info(f"Skipping non-TIF file: {file_name}")
        return {"message": "Skipped non-TIF file"}

    url = f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{task_id}/{file_id}"
    headers = {"Authorization": f"Bearer {token}"}
    file_path = f"temp_{file_name}"

    # Download file using AppEEARS API
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                # Make sure that the folder where the file will be saved exists.
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                logger.info(f"File {file_name} successfully downloaded to {file_path}")
            else:
                error_msg = await response.text()
                logger.error(f"Error downloading the file: {error_msg}")
                return {"error": f"Error downloading file: {error_msg}"}

    # Extracts information and coordinates
    data_points = extract_info_and_coordinates_from_tif(file_name, file_path)
    if not data_points:
        os.remove(file_path)
        return {"error": "Failed to extract data"}

    for point in data_points:
        result = await store_or_update_data_in_db(
            place_id=place_id,
            band=point['band'],
            value=point['value'],
            capture_date=point['date'],
            latitude=point['latitude'],
            longitude=point['longitude'],
            db=db
        )
    os.remove(file_path)
    return result

async def store_or_update_data_in_db(place_id: int, 
                                     band: str, 
                                     value: float, 
                                     capture_date: datetime, 
                                     latitude: float, 
                                     longitude: float, 
                                     db: AsyncSession
                                     ):
    
    point = WKTElement(f'POINT({longitude} {latitude})', srid=4326)
    logger.info(f"Buscando datos existentes para el lugar {place_id} con coordenadas {point} y fecha {capture_date}")
    statement = select(HarmonizedLandsatSentinelData).where(
        HarmonizedLandsatSentinelData.place_id == place_id,
        HarmonizedLandsatSentinelData.capture_date == capture_date,
        func.ST_DWithin(HarmonizedLandsatSentinelData.location, point, 1)  # 1 meter tolerance
    )
    result = await db.execute(statement)
    record = result.scalars().first()

    column_name = BAND_NAME_MAP.get(band.lower())  # Use the map to get the correct column name

    if record:
        setattr(record, column_name, value)  # Update using the mapped column name
    else:
        new_record_kwargs = {
            'place_id': place_id,
            'capture_date': capture_date,
            'location': point,
            column_name: value
        }
        new_record = HarmonizedLandsatSentinelData(**new_record_kwargs)
        db.add(new_record)

    await db.commit()
    logger.info("Data successfully processed and stored")
    return {"message": "Data processed successfully"}

def extract_info_and_coordinates_from_tif(filename: str, 
                                          file_path: str
                                          ):
    """Extracts the band, date and coordinates of each pixel from a GeoTIFF file."""
    
    logger.info(f"Extracting band and date information from the file {filename}")
    
    # Extracts band and date information from the filename
    match = re.search(r'B(\d+)_doy(\d{7})_', filename)
    if not match:
        logger.warning(f"Could not extract information from the file {filename}")
        return None

    band = f'b{int(match.group(1)):02}'  # Convert '1' to '01', '2' to '02', etc.
    doy = int(match.group(2)[-3:])  # Extracts the day of the year and converts to integer
    year = int(match.group(2)[:4])  # Extract the year
    date = datetime.strptime(f'{year}{doy}', '%Y%j').date()  # Convert to date

    data_points = []
    
    # Open the GeoTIFF file to read data and coordinates
    with rasterio.open(file_path) as src:
        # Gets the values of the first band
        band_data = src.read(1)
        
        for row in range(src.height):
            for col in range(src.width):
                value = band_data[row, col]
                # Gets the coordinates of the pixel
                longitude, latitude = src.xy(row, col)
                
                # Stores the band, date, coordinates and value in a list
                data_points.append({
                    'band': band,
                    'date': date,
                    'latitude': latitude,
                    'longitude': longitude,
                    'value': value
                })
                
    logger.info(f"Extracted information and coordinates for the file {filename}")
    return data_points

async def calculate_ndvi_for_place(db: AsyncSession, 
                                   place_id: int
                                   ):
    """Calculate NDVI for all recent records of a place."""
    
    recent_records = await db.execute(
        select(HarmonizedLandsatSentinelData)
        .where(HarmonizedLandsatSentinelData.place_id == place_id)
        .order_by(HarmonizedLandsatSentinelData.capture_date.desc())
    )
    records = recent_records.scalars().all()

    for record in records:
        if record.b05_nir and record.b04_red:  # Ensure both NIR and Red bands are present
            nir = record.b05_nir
            red = record.b04_red
            if (nir + red) != 0:
                ndvi = (nir - red) / (nir + red)
                record.ndvi = ndvi  # Set the NDVI value

    await db.commit()  # Commit changes after updating all records
    logger.info(f"NDVI calculated and updated for records of place ID {place_id}.")
