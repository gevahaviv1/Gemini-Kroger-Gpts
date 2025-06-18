from . import db

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
