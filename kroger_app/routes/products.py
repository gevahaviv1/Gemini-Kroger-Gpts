import logging
from flask import Blueprint, request, jsonify, current_app
from ..models import Product, PriceHistory
from kroger_app.services.products import process_product_data

logger = logging.getLogger(__name__)

products_bp = Blueprint("products", __name__)


@products_bp.route("/product/watch", methods=["POST"])
def upsert_product_and_alert():
    token = current_app.config.get("KROGER_TOKEN")
    if not token:
        return jsonify({"error": "Not authorized – please /login"}), 401
    data = request.get_json() or {}
    prod_data = data.get("product")
    if not prod_data:
        return jsonify({"error": "Missing 'product' object"}), 400
    pid = prod_data.get("id")
    if not pid:
        return jsonify({"error": "Missing product_id"}), 400
    result = process_product_data(prod_data)
    return jsonify(result), 200


@products_bp.route("/products", methods=["GET"])
def list_products():
    prods = Product.query.all()
    result = []
    for p in prods:
        result.append(
            {
                "id": p.id,
                "name": p.name,
                "brand": p.brand,
                "category": p.category,
                "regular_price": p.regular_price,
                "promo_price": p.promo_price,
                "stock_level": p.stock_level,
                "temperature_sensitive": p.temperature_sensitive,
            }
        )
    return jsonify(result), 200


@products_bp.route("/product/<product_id>/history", methods=["GET"])
def get_price_history(product_id):
    history = (
        PriceHistory.query.filter_by(product_id=product_id)
        .order_by(PriceHistory.timestamp.desc())
        .all()
    )
    return jsonify(
        [
            {
                "timestamp": h.timestamp.isoformat(),
                "promo_price": h.promo_price,
                "regular_price": h.regular_price,
            }
            for h in history
        ]
    )
