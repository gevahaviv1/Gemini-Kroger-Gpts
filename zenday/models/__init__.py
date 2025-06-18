from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy instance shared across models

db = SQLAlchemy()

from .product import Product  # noqa: E402
from .price_history import PriceHistory  # noqa: E402

__all__ = ["db", "Product", "PriceHistory"]
