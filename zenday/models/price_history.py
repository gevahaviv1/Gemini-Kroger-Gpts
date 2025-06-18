from datetime import datetime, timezone
from . import db
from .product import Product

class PriceHistory(db.Model):
    __tablename__ = "price_history"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    promo_price = db.Column(db.Float, nullable=False)
    regular_price = db.Column(db.Float, nullable=False)

    product = db.relationship("Product", backref="history")
