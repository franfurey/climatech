# app/external_apis/appears/harmonized_landsat_sentinel_data.py
import re
import os
import json
import requests
import rasterio
from datetime import datetime
from sqlalchemy.future import select
from geoalchemy2.shape import to_shape
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from shapely.geometry import mapping # This import is necessary to convert geometries from Shapely to GeoJSON.

from app.config.log_config import logger
from app.models import Place, HarmonizedLandsatSentinelData

BAND_NAME_MAP = {
    'b01': 'b01_coastal_aerosol',
    'b02': 'b02_blue',
    'b03': 'b03_green',
    'b04': 'b04_red',
    'b05': 'b05_nir',
    'b06': 'b06_swir1',
    'b07': 'b07_swir2',
    'b08': 'b08_nir_broad',
    'b8a': 'b8a_nir_narrow',
    'b09': 'b09_water_vapor',
    'b10': 'b10_cirrus',
    'b11': 'b11_swir1',
    'b12': 'b12_swir2',
    'fmask': 'fmask_quality_bits',
    'saa': 'saa_sun_azimuth',
    'sza': 'sza_sun_zenith',
    'vaa': 'vaa_view_azimuth',
    'vza': 'vza_view_zenith'
}

async def fetch_and_store_hls_data(place_id: int, db: AsyncSession, token) -> dict:
    logger.info(f"Fetching place information for place_id: {place_id}")
    statement = select(Place).where(Place.id == place_id)
    result = await db.execute(statement)
    place = result.scalars().first()
    
    if not place:
        logger.error(f"No place found with place_id: {place_id}")
        return {"error": "Place not found"}

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Un mes antes
    task_name = f"HarmonizedLandsatSentinelData-{end_date.strftime('%Y%m%d')}"

    logger.info(f"Submitting task for place_id {place_id} with task_name {task_name}")
    logger.info(f"Start date: {start_date.strftime('%m-%d-%Y')}, End date: {end_date.strftime('%m-%d-%Y')}")

    # Convertir la geometría de GeoAlchemy a Shapely y crear un FeatureCollection
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
        "fileName": "User-Drawn-Polygon"  # Asegúrate de ajustar este valor si es necesario
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

async def check_task_status(task_id: str, token: str) -> bool:
    """ Verifica el estado de la tarea y devuelve True si está completa. """
    logger.info(f"Verificando el estado de la tarea con ID: {task_id}")
    status_url = f"https://appeears.earthdatacloud.nasa.gov/api/task/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(status_url, headers=headers)
    if response.status_code == 200:
        task_info = response.json()
        task_status = task_info['status']
        logger.info(f"Estado de la tarea {task_id}: {task_status}")
        return task_status == 'done'
    else:
        logger.error(f"Error al verificar el estado de la tarea {task_id}: HTTP {response.status_code}")
    return False

async def list_task_files(task_id: str, token: str) -> list:
    """ Lista los archivos disponibles de una tarea completa. """
    logger.info(f"Listando archivos para la tarea con ID: {task_id}")
    url = f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = response.json()['files']
        logger.info(f"Archivos encontrados para la tarea {task_id}: {len(files)} archivos listados")
        return files
    else:
        logger.warning(f"No se pudieron listar los archivos para la tarea {task_id}: HTTP {response.status_code}")
        return []
    
import aiohttp
import asyncio
import os

async def download_and_process_file(
                                    task_id: str, 
                                    file_id: str, 
                                    file_name: str, 
                                    place_id: int, 
                                    db: AsyncSession,
                                    token: str
                                    ):
    """Descarga y procesa un archivo GeoTIFF utilizando la API de AppEEARS."""
    url = f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{task_id}/{file_id}"
    headers = {"Authorization": f"Bearer {token}"}
    file_path = f"temp_{file_name}"

    # Descargar archivo usando AppEEARS API
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                # Asegúrate de que la carpeta donde se guardará el archivo existe
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                logger.info(f"Archivo {file_name} descargado exitosamente a {file_path}")
            else:
                error_msg = await response.text()
                logger.error(f"Error descargando el archivo: {error_msg}")
                return {"error": f"Error downloading file: {error_msg}"}

    # Extrae información y coordenadas
    data_points = extract_info_and_coordinates_from_tif(file_name, file_path)
    if not data_points:
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
        logger.info(f"Dato procesado y almacenado para {file_name}, coordenadas ({point['latitude']}, {point['longitude']})")
    return result

from geoalchemy2.elements import WKTElement
from sqlalchemy.sql import func

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
        func.ST_DWithin(HarmonizedLandsatSentinelData.location, point, 1)  # 1 metro de tolerancia
    )
    result = await db.execute(statement)
    record = result.scalars().first()

    column_name = BAND_NAME_MAP.get(band.lower())  # Usa el mapa para obtener el nombre de columna correcto

    if record:
        logger.info(f"Actualizando registro existente con nueva banda {band} y valor {value}")
        setattr(record, column_name, value)  # Actualiza usando el nombre de columna mapeado
    else:
        logger.info(f"Creando nuevo registro para banda {band} con valor {value}")
        new_record_kwargs = {
            'place_id': place_id,
            'capture_date': capture_date,
            'location': point,
            column_name: value
        }
        new_record = HarmonizedLandsatSentinelData(**new_record_kwargs)
        db.add(new_record)

    await db.commit()
    logger.info("Datos procesados y almacenados exitosamente")
    return {"message": "Data processed successfully"}

import rasterio
import re
from datetime import datetime

def extract_info_and_coordinates_from_tif(filename: str, file_path: str):
    """Extrae la banda, fecha y las coordenadas de cada píxel de un archivo GeoTIFF."""
    logger.info(f"Extrayendo información de banda y fecha del archivo {filename}")
    
    # Extrae información de banda y fecha del nombre del archivo
    match = re.search(r'B(\d+)_doy(\d{7})_', filename)
    if not match:
        logger.warning(f"No se pudo extraer información del archivo {filename}")
        return None

    band = f'b{int(match.group(1)):02}'  # Convierte '1' a '01', '2' a '02', etc.
    doy = int(match.group(2)[-3:])  # Extrae el día del año y convierte a entero
    year = int(match.group(2)[:4])  # Extrae el año
    date = datetime.strptime(f'{year}{doy}', '%Y%j').date()  # Convierte a fecha

    data_points = []
    
    # Abre el archivo GeoTIFF para leer datos y coordenadas
    with rasterio.open(file_path) as src:
        # Obtiene los valores de la primera banda
        band_data = src.read(1)
        
        for row in range(src.height):
            for col in range(src.width):
                value = band_data[row, col]
                # Obtiene las coordenadas del píxel
                longitude, latitude = src.xy(row, col)
                
                # Almacena la banda, fecha, coordenadas y valor en una lista
                data_points.append({
                    'band': band,
                    'date': date,
                    'latitude': latitude,
                    'longitude': longitude,
                    'value': value
                })
                
    logger.info(f"Extraída información y coordenadas para el archivo {filename}")
    return data_points
