"""
Kroger Cart API operations module.
"""
import os
import requests
from typing import Dict, List, Optional

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
    
    print(f"\n--- DEBUG: GET CART ---")
    print(f"Token first 20 chars: {access_token[:20]}...")
    print(f"Headers: {headers}")
    
    try:
        # If cart_id is provided, get that specific cart, otherwise get the default cart
        url = f"https://api.kroger.com/v1/cart/{cart_id}" if cart_id else "https://api.kroger.com/v1/cart"
        print(f"Request URL: {url}")
        response = requests.get(url, headers=headers)
        print(f"Response status: {response.status_code}")
        
        # Try to print the response body, but handle any parsing errors
        try:
            print(f"Response body: {response.text[:200]}...")
        except:
            print("Could not print response body")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Exception: {str(e)}")
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:200]}...")
            
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
    
    print(f"\n--- DEBUG: CREATE CART ---")
    print(f"Token first 20 chars: {access_token[:20]}...")
    print(f"Headers: {headers}")
    print(f"Raw items: {items}")
    
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
    
    print(f"Formatted items: {formatted_items}")
    
    data = {
        "items": formatted_items
    }
    
    print(f"Request body: {data}")
    
    try:
        url = "https://api.kroger.com/v1/cart"
        print(f"Request URL: {url}")
        
        response = requests.post(
            url,
            headers=headers,
            json=data
        )
        
        print(f"Response status: {response.status_code}")
        try:
            print(f"Response body: {response.text[:200]}...")
        except:
            print("Could not print response body")
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Exception: {str(e)}")
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:200]}...")
            
            if e.response.status_code == 401:
                raise Exception("Unauthorized: Please check your API credentials and ensure you have cart access")
            elif e.response.status_code == 403:
                raise Exception("Forbidden: Your token doesn't have the required cart.basic scope")
            elif e.response.status_code == 400:
                raise Exception(f"Bad request: {e.response.json().get('reason', 'Unknown error')}")
        raise Exception(f"Cart API error: {str(e)}")

def add_to_cart(access_token: str, cart_id: str, items: List[Dict], modality: str = "PICKUP") -> Dict:
    """
    Add items to an existing cart.
    
    Args:
        access_token: OAuth2 access token
        cart_id: Cart ID to add items to
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
    
    print(f"\n--- DEBUG: ADD TO CART ---")
    print(f"Token first 20 chars: {access_token[:20]}...")
    print(f"Cart ID: {cart_id}")
    print(f"Headers: {headers}")
    print(f"Raw items: {items}")
    
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
    
    print(f"Formatted items: {formatted_items}")
    
    try:
        # Add items one by one to the cart
        results = []
        for item in formatted_items:
            url = f"https://api.kroger.com/v1/cart/{cart_id}/items"
            print(f"Request URL: {url}")
            print(f"Request body: {item}")
            
            response = requests.put(
                url,
                headers=headers,
                json=item
            )
            
            print(f"Response status: {response.status_code}")
            try:
                print(f"Response body: {response.text[:200]}...")
            except:
                print("Could not print response body")
                
            response.raise_for_status()
            results.append(response.json())
        
        return {"results": results}
    except requests.exceptions.RequestException as e:
        print(f"Exception: {str(e)}")
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:200]}...")
            
            if e.response.status_code == 401:
                raise Exception("Unauthorized: Please check your API credentials and ensure you have cart access")
            elif e.response.status_code == 403:
                raise Exception("Forbidden: Your token doesn't have the required cart.basic scope")
            elif e.response.status_code == 400:
                raise Exception(f"Bad request: {e.response.json().get('reason', 'Unknown error')}")
            elif e.response.status_code == 404:
                raise Exception(f"Cart not found: {cart_id}")
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
