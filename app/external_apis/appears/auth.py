import requests

import logging
# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # Crea una instancia de logger para usar en todo el módulo

def get_appears_token(username: str, password: str) -> str:
    url = "https://appeears.earthdatacloud.nasa.gov/api/login"
    response = requests.post(url, auth=(username, password))
    if response.status_code == 200:
        token = response.json()['token']
        logger.info(f"Token: {token}")
        return token
    else:
        raise Exception("Authentication failed")