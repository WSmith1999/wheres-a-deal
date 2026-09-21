import requests
import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
auth_url = "https://api.kroger.com/v1/connect/oauth2/token"
base_url = "https://api.kroger.com/v1"
def get_token():
    payload = {
        "grant_type": "client_credentials",
        "scope":"product.compact"
    }
    try:
        response = requests.post(
            auth_url,
            data = payload,
            auth=(client_id, client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"failed to access {e} ")
        return None


# get the location id in order to get prices 
def location_search(token, zipcode, distance=5, limit=1):
    url = f"{base_url}/locations"
    headers = {
        "Accept": "application/json",
        "Authorization": f"bearer {token}"

    }
    params = {
        "filter.zipCode.near":zipcode,
        "filter.radiusInMiles":distance,
        "filter.limit":limit
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch due to {e}")
        return None


def api_search(token, term, locationid, limit=4):
    url = f"{base_url}/products"
    headers = {
        "Content-Type":"application/json",
        "Authorization":f"bearer {token}"
    }
    params = {
        "filter.term":term,
        "filter.limit":limit,
        "filter.locationId":locationid
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch due to {e}")
        return None
    
def id_specific_search(token, item_id, locationid, limit=1):
    url = f"{base_url}/products"
    headers = {
        "Content-Type":"application/json",
        "Authorization":f"bearer {token}"
    }
    params = {
        "filter.limit":limit,
        "filter.locationId":locationid,
        "filter.productId":item_id
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch due to {e}")
        print("Kroger response:", response.text)
        return None

def promo_or_regular(api_product):
    price_data = api_product["items"][0]["price"]
    regular = price_data["regular"]
    promo = price_data.get("promo")

    if not promo:
        return regular

    if promo > 0 and promo < regular:
        return promo

    return regular

