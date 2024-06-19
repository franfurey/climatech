import requests

def get_appears_token(username: str, password: str) -> str:
    url = "https://appeears.earthdatacloud.nasa.gov/api/login"
    response = requests.post(url, auth=(username, password))
    if response.status_code == 200:
        return response.json()['token']
    else:
        raise Exception("Authentication failed")