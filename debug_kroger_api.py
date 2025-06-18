#!/usr/bin/env python3
"""
Debug script for testing Kroger API connectivity directly.
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_FILE = 'token.json'

def get_token():
    """Read token from file."""
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('access_token') or data.get('token')
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def test_cart_connection():
    """Test connectivity to the Kroger cart API."""
    token = get_token()
    if not token:
        print("No token found. Please authenticate first.")
        return
    
    print(f"Token found (first 20 chars): {token[:20]}...")
    
    # Headers
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 1. Try to get the cart
    print("\n--- Testing GET /cart ---")
    try:
        response = requests.get(
            "https://api.kroger.com/v1/cart",
            headers=headers
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # 2. Try to create a cart
    print("\n--- Testing POST /cart ---")
    try:
        # Headers with content type
        post_headers = headers.copy()
        post_headers["Content-Type"] = "application/json"
        
        # Test payload
        data = {
            "items": [
                {
                    "upc": "0001111041700",
                    "quantity": 1,
                    "allowSubstitutes": True,
                    "modality": "PICKUP"
                }
            ]
        }
        
        response = requests.post(
            "https://api.kroger.com/v1/cart",
            headers=post_headers,
            json=data
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_cart_connection()
