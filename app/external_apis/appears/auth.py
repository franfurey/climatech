import aiohttp
import requests

from app.config.log_config import logger

def get_appears_token(username: str, password: str) -> str:
    url = "https://appeears.earthdatacloud.nasa.gov/api/login"
    response = requests.post(url, auth=(username, password))
    if response.status_code == 200:
        token = response.json()['token']
        logger.info(f"Token: {token}")
        return token
    else:
        raise Exception("Authentication failed")
    
async def get_aws_credentials(username: str, password: str):
    """Obtiene credenciales temporales de AWS para acceder a S3 de forma asíncrona."""
    url = "https://appeears.earthdatacloud.nasa.gov/api/s3credentials"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, auth=aiohttp.BasicAuth(username, password), headers={"Content-Length": "0"}) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                error_message = await response.text()
                logger.error(f"Failed to obtain AWS credentials: HTTP {response.status} - {error_message}")
                return {"error": f"Failed to obtain credentials: {error_message}"}