import logging
import requests
from typing import Dict, Optional
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

        logger.info(f"Request URL: {url}")
        logger.info(f"Request Headers: {headers}")

        response = requests.get(url, headers=headers)
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Text: {response.text}")

        success = handle_kroger_api_response(response, 204, "Got cart.")["success"]
        if success:
            return response.json()
    except requests.exceptions.RequestException as e:
        handle_kroger_request_exception(e)
    except Exception as e:
        raise


def add_to_cart(access_token: str, item: Dict) -> Dict:
    """
    Add items to the Kroger cart using the /v1/cart/add endpoint.
    Args:
        access_token: OAuth2 access token
        item: Item to add, with format:
            {
                "upc": "0001111041700",
                "quantity": 1,
                "modality": "PICKUP" (optional)
            }
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Need to convert to adding items - missing dependencies
    formatted_item = [
        {
            "upc": item.get("upc"),
            "quantity": item.get("quantity", 1),
            "modality": item.get("modality", "PICKUP"),
        }
    ]
    data = {"items": formatted_item}

    try:
        response = requests.put(
            "https://api.kroger.com/v1/cart/add", headers=headers, json=data
        )

        response = handle_kroger_api_response(response, 204, "Item(s) added to cart.")
        if response["success"]:
            return response
    except requests.exceptions.RequestException as e:
        handle_kroger_request_exception(e)
    except Exception as e:
        raise


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
