from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy instance shared across models

db = SQLAlchemy()

from .product import Product
from .price_history import PriceHistory

__all__ = ["db", "Product", "PriceHistory"]
