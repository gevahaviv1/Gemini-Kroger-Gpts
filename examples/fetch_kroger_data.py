"""Convenience wrapper for kroger_api service."""
from kroger_app.services.kroger_api import (
    get_access_token,
    fetch_nearest_location,
    fetch_products,
)

__all__ = [
    "get_access_token",
    "fetch_nearest_location",
    "fetch_products",
]

if __name__ == "__main__":
    token = get_access_token()
    loc = fetch_nearest_location(token)
    print("Nearest location:", loc)
    items = fetch_products(token, term="milk", limit=5, location_id=loc.get("locationId"))
    print("Fetched", len(items), "items")
