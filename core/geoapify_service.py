import os
import requests

GEOAPIFY_KEY = os.environ.get('GEOAPIFY_KEY')
BASE_AUTOCOMPLETE_URL = 'https://api.geoapify.com/v1/geocode/autocomplete'


def search_places(query: str, limit: int = 6):
    """Search places using Geoapify autocomplete. Returns a list of simplified dicts.

    Each dict contains: name, formatted, raw (original feature)
    """
    if not query:
        return []
    if not GEOAPIFY_KEY:
        raise RuntimeError('Geoapify API key not set (GEOAPIFY_KEY)')

    params = {
        'text': query,
        'limit': limit,
        'apiKey': GEOAPIFY_KEY
    }

    resp = requests.get(BASE_AUTOCOMPLETE_URL, params=params, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    features = payload.get('features') or []

    results = []
    for f in features:
        props = f.get('properties') or {}
        name = props.get('name') or props.get('address_line1') or props.get('formatted') or ''
        formatted = props.get('formatted') or props.get('address_line1') or ''
        results.append({
            'name': name,
            'formatted': formatted,
            'raw': f
        })

    return results
