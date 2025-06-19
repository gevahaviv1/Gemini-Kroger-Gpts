import logging
import requests
from typing import Dict, List, Optional
from kroger_app.utils import handle_kroger_api_response, handle_kroger_request_exception


logger = logging.getLogger(__name__)


def get_cart(access_token: str, cart_id: Optional[str] = None) -> Dict:
    """Get the contents of a cart.

    Args:
        access_token: OAuth2 access token
        cart_id: Optional cart ID. If provided, gets a specific cart, otherwise gets the default cart
    """
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}

    try:
        url = (
            f"https://api.kroger.com/v1/cart/{cart_id}"
            if cart_id
            else "https://api.kroger.com/v1/cart"
        )

        response = requests.get(url, headers=headers)

        try:
            logger.info(f"Response body: {response.text[:200]}...")
        except:
            logger.info("Could not print response body")

        return handle_kroger_api_response(response)
    except requests.exceptions.RequestException as e:
        handle_kroger_request_exception(e)


def add_to_cart(access_token: str, items: List[Dict], modality: str = "PICKUP") -> Dict:
    """
    Add items to the Kroger cart using the /v1/cart/add endpoint.
    Args:
        access_token: OAuth2 access token
        items: List of items to add, each with format:
            {
                "upc": "0001111041700",
                "quantity": 1,
                "modality": "PICKUP" (optional)
            }
        modality: Fulfillment type (PICKUP or DELIVERY)
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    formatted_items = [
        {
            "upc": item.get("upc") or item.get("productId"),
            "quantity": item.get("quantity", 1),
            "modality": item.get("modality", modality),
        }
        for item in items
    ]
    data = {"items": formatted_items}

    try:
        response = requests.put(
            "https://api.kroger.com/v1/cart/add", headers=headers, json=data
        )
        return handle_kroger_api_response(response)
    except requests.exceptions.RequestException as e:
        handle_kroger_request_exception(e)


def remove_from_cart(access_token: str, cart_id: str, upc: str) -> Dict:
    """Remove an item from the cart.

    Args:
        access_token: OAuth2 access token
        cart_id: Cart ID
        upc: UPC of the item to remove
    """
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}

    try:
        response = requests.delete(
            f"https://api.kroger.com/v1/cart/{cart_id}/items/{upc}", headers=headers
        )
        return handle_kroger_api_response(response)
    except requests.exceptions.RequestException as e:
        handle_kroger_request_exception(e)
                    "Forbidden: Your token doesn't have the required cart.basic scope"
                )
            elif e.response.status_code == 400:
                raise Exception(
                    f"Bad request: {e.response.json().get('reason', 'Unknown error')}"
                )
            elif e.response.status_code == 404:
                raise Exception(f"Item or cart not found")
        raise Exception(f"Cart API error: {str(e)}")
