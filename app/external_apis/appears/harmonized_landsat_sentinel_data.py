import re
import os
import json
import requests
import rasterio
from datetime import datetime
from rasterio.plot import show
from sqlalchemy.future import select
from geoalchemy2.shape import to_shape
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from shapely.geometry import mapping # This import is necessary to convert geometries from Shapely to GeoJSON.

from app.models import Place, HarmonizedLandsatSentinelData
from app.external_apis.appears.auth import get_appears_token

import boto3
from botocore.exceptions import NoCredentialsError

import logging
# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # Crea una instancia de logger para usar en todo el módulo

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

async def download_and_process_file(file_url: str, file_name: str, place_id: int, db: AsyncSession):
    """ Descarga y procesa un archivo GeoTIFF. """
    logger.info(f"Descargando archivo: {file_name} desde {file_url}")
    
    # Configura el cliente de S3
    s3 = boto3.client('s3')
    
    # Extrae el bucket y la key del archivo desde la URL
    bucket = file_url.split('/')[2]
    key = '/'.join(file_url.split('/')[3:])
    
    file_path = f"temp_{file_name}"
    try:
        s3.download_file(Bucket=bucket, Key=key, Filename=file_path)
        logger.info(f"Archivo {file_name} descargado exitosamente")
    except NoCredentialsError:
        logger.error("Credenciales de AWS no disponibles")
        return {"error": "AWS credentials not found"}
    except Exception as e:
        logger.error(f"Error descargando el archivo: {str(e)}")
        return {"error": "Error downloading file"}

    band, capture_date = extract_info_from_filename(file_name)
    if not band or not capture_date:
        logger.error("Nombre de archivo inválido para procesamiento")
        return {"error": "Invalid file name for processing"}

    # Procesa el archivo descargado
    with rasterio.open(file_path) as src:
        value = src.read(1)[0, 0]  # Leer el primer valor de la primera banda

    result = await store_or_update_data_in_db(place_id=place_id, band=band, value=value, capture_date=capture_date, db=db)
    logger.info(f"Dato procesado y almacenado para {file_name}")
    return result

async def store_or_update_data_in_db(place_id: int, band: str, value: float, capture_date: datetime, db: AsyncSession):
    """ Busca si existe un registro con la misma fecha y lugar; si sí, actualiza, si no, crea uno nuevo. """
    logger.info(f"Buscando datos existentes para el lugar {place_id} en la fecha {capture_date}")
    statement = select(HarmonizedLandsatSentinelData).where(
        HarmonizedLandsatSentinelData.place_id == place_id,
        HarmonizedLandsatSentinelData.capture_date == capture_date
    )
    result = await db.execute(statement)
    record = result.scalars().first()

    if record:
        logger.info(f"Actualizando registro existente con nueva banda {band} y valor {value}")
        setattr(record, band, value)  # Actualiza el campo correspondiente a la banda
    else:
        logger.info(f"Creando nuevo registro para banda {band} con valor {value}")
        # Crea un nuevo registro si no existe
        new_record = HarmonizedLandsatSentinelData(
            place_id=place_id,
            capture_date=capture_date,
            **{band: value}
        )
        db.add(new_record)
    
    await db.commit()
    logger.info("Datos procesados y almacenados exitosamente")
    return {"message": "Data processed successfully"}

def extract_info_from_filename(filename: str):
    """ Extrae la fecha y la banda del nombre del archivo GeoTIFF. """
    logger.info(f"Extrayendo información de banda y fecha del archivo {filename}")
    match = re.search(r'B(\d+)_doy(\d{7})_', filename)
    if match:
        band = f'b{int(match.group(1)):02}'  # Convierte '1' a '01', '2' a '02', etc.
        doy = int(match.group(2)[-3:])  # Extrae el día del año y convierte a entero
        year = int(match.group(2)[:4])  # Extrae el año
        date = datetime.strptime(f'{year}{doy}', '%Y%j').date()  # Convierte a fecha
        logger.info(f"Extraído banda {band} y fecha {date} del archivo")
        return band, date
    else:
        logger.warning(f"No se pudo extraer información del archivo {filename}")
    return None, None
