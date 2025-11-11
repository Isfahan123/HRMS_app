import os
import uuid
import requests

# Geoapify configuration
GEOAPIFY_API_KEY = "c664905ab3824cde9203a35f4804ecdd"
AUTOCOMPLETE_URL = "https://api.geoapify.com/v1/geocode/autocomplete"

def new_session_token():
    # Session token not required for Geoapify billing grouping, but keep same API for widget
    return str(uuid.uuid4())

def autocomplete_cities(query: str, session_token: str, country_restriction: str | None = None):
    """Return list of {description, place_id} using Geoapify.

    place_id maps to Geoapify's feature 'place_id'.
    """
    if not GEOAPIFY_API_KEY or not query:
        return []
    params = {
        "text": query,
        "apiKey": GEOAPIFY_API_KEY,
        "type": "city",
        "limit": 7,
    }
    if country_restriction:
        params["filter"] = f"countrycode:{country_restriction.lower()}"
    try:
        r = requests.get(AUTOCOMPLETE_URL, params=params, timeout=6)
        r.raise_for_status()
        data = r.json()
        features = data.get("features", [])
        results = []
        for f in features:
            props = f.get("properties", {})
            desc_parts = [
                props.get("city") or props.get("name"),
                props.get("state"),
                props.get("country")
            ]
            description = ", ".join([p for p in desc_parts if p])
            results.append({
                "description": description,
                "place_id": str(props.get("place_id")),
                "raw": props,
            })
        return results
    except Exception:
        return []

def place_details(place_id: str, session_token: str):
    # Not strictly needed now; could call details endpoint if required later.
    return {}
 
