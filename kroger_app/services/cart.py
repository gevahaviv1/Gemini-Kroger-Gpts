"""
Kroger Cart API operations module.
"""
import os
import logging
import requests
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# The get_cart_token function is not needed based on the documentation
# The OAuth2 token is used directly for cart operations

def get_cart(access_token: str, cart_id: Optional[str] = None) -> Dict:
    """Get the contents of a cart.
    
    Args:
        access_token: OAuth2 access token
        cart_id: Optional cart ID. If provided, gets a specific cart, otherwise gets the default cart
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    logger.info("--- DEBUG: GET CART ---")
    logger.info(f"Token first 20 chars: {access_token[:20]}...")
    logger.info(f"Headers: {headers}")
    
    try:
        # If cart_id is provided, get that specific cart, otherwise get the default cart
        url = f"https://api.kroger.com/v1/cart/{cart_id}" if cart_id else "https://api.kroger.com/v1/cart"
        logger.info(f"Request URL: {url}")
        response = requests.get(url, headers=headers)
        logger.info(f"Response status: {response.status_code}")
        
        # Try to print the response body, but handle any parsing errors
        try:
            logger.info(f"Response body: {response.text[:200]}...")
        except:
            logger.info("Could not print response body")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception: {str(e)}")
        if e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text[:200]}...")
            
            if e.response.status_code == 401:
                raise Exception("Unauthorized: Please check your API credentials and ensure you have cart access")
            elif e.response.status_code == 403:
                raise Exception("Forbidden: Your token doesn't have the required cart.basic scope")
            elif e.response.status_code == 404:
                raise Exception("Cart not found")
        raise Exception(f"Cart API error: {str(e)}")

def create_cart(access_token: str, items: List[Dict], modality: str = "PICKUP") -> Dict:
    """
    Create a new cart with items.
    
    Args:
        access_token: OAuth2 access token
        items: List of items to add, each with format:
            {
                "upc": "0001111041700",
                "quantity": 1,
                "allowSubstitutes": True,
                "specialInstructions": "Optional instructions"
            }
        modality: Fulfillment type (PICKUP or DELIVERY)
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    logger.info("--- DEBUG: CREATE CART ---")
    logger.info(f"Token first 20 chars: {access_token[:20]}...")
    logger.info(f"Headers: {headers}")
    logger.info(f"Raw items: {items}")
    
    # Transform items to the format expected by the API
    formatted_items = []
    for item in items:
        formatted_item = {
            "upc": item.get("upc") or item.get("productId"),  # Support both formats
            "quantity": item.get("quantity", 1),
            "allowSubstitutes": item.get("allowSubstitutes", True),
            "modality": modality
        }
        
        # Add special instructions if provided
        if "specialInstructions" in item:
            formatted_item["specialInstructions"] = item["specialInstructions"]
            
        formatted_items.append(formatted_item)
    
    logger.info(f"Formatted items: {formatted_items}")
    
    data = {
        "items": formatted_items
    }
    
    logger.info(f"Request body: {data}")
    
    try:
        url = "https://api.kroger.com/v1/cart"
        logger.info(f"Request URL: {url}")
        
        response = requests.post(
            url,
            headers=headers,
            json=data
        )
        
        logger.info(f"Response status: {response.status_code}")
        try:
            logger.info(f"Response body: {response.text[:200]}...")
        except:
            logger.info("Could not print response body")
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception: {str(e)}")
        if e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text[:200]}...")
            
            if e.response.status_code == 401:
                raise Exception("Unauthorized: Please check your API credentials and ensure you have cart access")
            elif e.response.status_code == 403:
                raise Exception("Forbidden: Your token doesn't have the required cart.basic scope")
            elif e.response.status_code == 400:
                raise Exception(f"Bad request: {e.response.json().get('reason', 'Unknown error')}")
        raise Exception(f"Cart API error: {str(e)}")

def add_to_cart(access_token: str, cart_id: str, items: List[Dict], modality: str = "PICKUP") -> Dict:
    """
    Add items to the Kroger cart using the /v1/cart/add endpoint.
    Args:
        access_token: OAuth2 access token
        cart_id: (ignored, for compatibility)
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
        "Content-Type": "application/json"
    }
    logger.info("--- DEBUG: ADD TO CART (v1/cart/add) ---")
    logger.info(f"Token first 20 chars: {access_token[:20]}...")
    logger.info(f"Headers: {headers}")
    logger.info(f"Raw items: {items}")
    # Format items for the API
    formatted_items = []
    for item in items:
        formatted_item = {
            "upc": item.get("upc") or item.get("productId"),
            "quantity": item.get("quantity", 1),
            "modality": item.get("modality", modality)
        }
        formatted_items.append(formatted_item)
    data = {"items": formatted_items}
    logger.info(f"Request body: {data}")
    try:
        response = requests.put(
            "https://api.kroger.com/v1/cart/add",
            headers=headers,
            json=data
        )
        logger.info(f"Response status: {response.status_code}")
        try:
            logger.info(f"Response body: {response.text[:200]}...")
        except:
            logger.info("Could not print response body")
        if response.status_code == 204:
            return {"success": True, "message": "Item(s) added to cart."}
        elif response.status_code == 401:
            raise Exception("Unauthorized: Please check your API credentials and ensure you have cart access")
        elif response.status_code == 403:
            raise Exception("Forbidden: Your token doesn't have the required cart.basic scope")
        elif response.status_code == 400:
            try:
                return {"error": response.json()}
            except Exception:
                return {"error": response.text}
        else:
            try:
                return {"error": response.json()}
            except Exception:
                return {"error": response.text}
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception: {str(e)}")
        if e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text[:200]}...")
            if e.response.status_code == 401:
                raise Exception("Unauthorized: Please check your API credentials and ensure you have cart access")
            elif e.response.status_code == 403:
                raise Exception("Forbidden: Your token doesn't have the required cart.basic scope")
            elif e.response.status_code == 400:
                raise Exception(f"Bad request: {e.response.json().get('reason', 'Unknown error')}")
            elif e.response.status_code == 404:
                raise Exception("Cart not found")
        raise Exception(f"Cart API error: {str(e)}")

def remove_from_cart(access_token: str, cart_id: str, upc: str) -> Dict:
    """Remove an item from the cart.
    
    Args:
        access_token: OAuth2 access token
        cart_id: Cart ID
        upc: UPC of the item to remove
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        # DELETE method removes the item
        response = requests.delete(
            f"https://api.kroger.com/v1/cart/{cart_id}/items/{upc}",
            headers=headers
        )
        response.raise_for_status()
        return {"success": True, "message": f"Item {upc} removed from cart {cart_id}"}
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            if e.response.status_code == 401:
                raise Exception("Unauthorized: Please check your API credentials and ensure you have cart access")
            elif e.response.status_code == 403:
                raise Exception("Forbidden: Your token doesn't have the required cart.basic scope")
            elif e.response.status_code == 400:
                raise Exception(f"Bad request: {e.response.json().get('reason', 'Unknown error')}")
            elif e.response.status_code == 404:
                raise Exception(f"Item or cart not found")
        raise Exception(f"Cart API error: {str(e)}")
