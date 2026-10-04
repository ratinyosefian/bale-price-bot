import requests
from config import SERVIX_API_KEY


def get_prices():
    url = "https://servix.cc/api/v1/assets"

    headers = {
        "X-API-Key": SERVIX_API_KEY
    }

    response = requests.get(url, headers=headers, timeout=10)

    response.raise_for_status()

    return response.json()