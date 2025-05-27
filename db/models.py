from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    brand = db.Column(db.String)
    category = db.Column(db.String)
    image_url = db.Column(db.String)
    product_url = db.Column(db.String)
    regular_price = db.Column(db.Float)
    promo_price = db.Column(db.Float)
    fulfillment = db.Column(db.JSON)
    stock_level = db.Column(db.String)
    size = db.Column(db.String)
    sold_by = db.Column(db.String)
    location = db.Column(db.JSON)
    dimensions = db.Column(db.JSON)
    temperature_sensitive = db.Column(db.Boolean)


class PriceHistory(db.Model):
    __tablename__ = "price_history"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    promo_price = db.Column(db.Float, nullable=False)
    regular_price = db.Column(db.Float, nullable=False)

    product = db.relationship("Product", backref="history")
