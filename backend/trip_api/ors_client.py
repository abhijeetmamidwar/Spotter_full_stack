import requests
from django.conf import settings

import polyline


BASE_URL = "https://api.openrouteservice.org"


def geocode_address(address):
    url = f"{BASE_URL}/geocode/search"
    params = {
        "api_key": settings.ORS_API_KEY,
        "text": address
    }
    res = requests.get(url, params=params)
    data = res.json()

    if "features" not in data or not data["features"]:
        raise ValueError(f"Address not found: {address}")

    coords = data["features"][0]["geometry"]["coordinates"]
    # ORS gives [lng, lat]
    return {"lat": coords[1], "lng": coords[0]}


def get_route(coord_list):
    url = f"{BASE_URL}/v2/directions/driving-car"
    
    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json"
    }

    params = {
        "api_key": settings.ORS_API_KEY
    }

    body = {
        "coordinates": coord_list,
        "instructions": False,
        # "geometry_format": "geojson"
        "geometry_simplify": False
    }

    res = requests.post(url, params=params, json=body, headers=headers)
    data = res.json()

    if "routes" not in data or not data["routes"]:
        raise ValueError("No route found")

    route = data["routes"][0]

    # polyline.decode → returns [lat, lng]
    decoded = polyline.decode(route["geometry"])

    # Convert to ORS format [lng, lat] so frontend can convert properly
    polyline_coords = [[lng, lat] for lat, lng in decoded]

    return {
        "distance_meters": route["summary"]["distance"],
        "duration_seconds": route["summary"]["duration"],
        "geometry": polyline_coords
    }
