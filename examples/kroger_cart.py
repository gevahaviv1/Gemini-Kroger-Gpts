"""Convenience wrapper for cart service."""
from kroger_app.services.cart import (
    get_cart,
    create_cart,
    add_to_cart,
    remove_from_cart,
)

__all__ = [
    "get_cart",
    "create_cart",
    "add_to_cart",
    "remove_from_cart",
]

# Example usage when run directly
if __name__ == "__main__":
    import os
    from kroger_app.services.kroger_api import get_access_token

    token = get_access_token()
    cart = get_cart(token)
    print("Cart data:", cart)
