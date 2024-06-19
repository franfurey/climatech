import requests

def get_product_info(token: str, product_id: str) -> dict:
    headers = {'Authorization': f'Bearer {token}'}
    url = f"https://appeears.earthdatacloud.nasa.gov/api/product/{product_id}"
    response = requests.get(url, headers=headers)
    return response.json()