"""
Kroger Cart API operations module.
"""
import os
import requests
from typing import Dict, List, Optional

def get_cart_token(access_token: str) -> str:
    """Get a cart-specific token for cart operations."""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(
        "https://api.kroger.com/v1/cart/token",
        headers=headers
    )
    response.raise_for_status()
    return response.json().get("token")

def get_cart(access_token: str, location_id: str) -> Dict:
    """Get the current cart contents."""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(
        f"https://api.kroger.com/v1/cart?locationId={location_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()

def add_to_cart(access_token: str, location_id: str, items: List[Dict]) -> Dict:
    """
    Add items to cart.
    
    Args:
        access_token: Kroger API access token
        location_id: Store location ID
        items: List of items to add, each with format:
            {
                "productId": "0001111041700",
                "quantity": 1
            }
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "items": items,
        "locationId": location_id
    }
    
    response = requests.put(
        "https://api.kroger.com/v1/cart/add",
        headers=headers,
        json=data
    )
    response.raise_for_status()
    return response.json()

def remove_from_cart(access_token: str, location_id: str, item_id: str) -> Dict:
    """Remove an item from the cart."""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "items": [{
            "productId": item_id,
            "quantity": 0  # Setting quantity to 0 removes the item
        }],
        "locationId": location_id
    }
    
    response = requests.put(
        "https://api.kroger.com/v1/cart/add",  # Same endpoint as add, but quantity=0
        headers=headers,
        json=data
    )
    response.raise_for_status()
    return response.json()
