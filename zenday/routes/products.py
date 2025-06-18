import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from ..models import db, Product, PriceHistory
from ..services.kroger_api import fetch_products, fetch_nearest_location, get_access_token
from ..mappers.kroger import map_kroger_to_zenday

logger = logging.getLogger(__name__)

products_bp = Blueprint('products', __name__)

WATCHED_IDS = ["0001111041700"]


def process_product_data(prod_data):
    pid = prod_data["id"]
    new_reg = prod_data["price"]["regular"]
    new_pr = prod_data["price"]["promo"]

    existing = Product.query.get(pid)

    if existing:
        old_pr = existing.promo_price or 0
        new_pr = old_pr - 0.1

        if new_pr is not None and new_pr < old_pr:
            existing.regular_price = new_reg
            existing.promo_price = new_pr
            db.session.add(existing)
            history = PriceHistory(product_id=pid, promo_price=new_pr, regular_price=new_reg)
            db.session.add(history)
            logger.info(f"✅ Polled prices at {datetime.utcnow().isoformat()}")
            db.session.commit()
            logger.info(f"🔔 Price drop for {pid}: {old_pr} → {new_pr}")
            return {"alert": True, "old_price": old_pr, "new_price": new_pr}

        history = PriceHistory(product_id=pid, promo_price=new_pr, regular_price=new_reg)
        db.session.add(history)
        logger.info(f"✅ Polled prices at {datetime.utcnow().isoformat()}")
        db.session.commit()
        return {"alert": False}

    new_p = Product(
        id=pid,
        name=prod_data.get("name"),
        brand=prod_data.get("brand"),
        category=prod_data.get("category"),
        image_url=prod_data.get("image_url"),
        product_url=prod_data.get("product_url"),
        regular_price=new_reg,
        promo_price=new_pr,
        fulfillment=prod_data.get("fulfillment"),
        stock_level=prod_data.get("stock_level"),
        size=prod_data.get("size"),
        sold_by=prod_data.get("sold_by"),
        location=prod_data.get("location"),
        dimensions=prod_data.get("dimensions"),
        temperature_sensitive=prod_data.get("temperature_sensitive"),
    )
    db.session.add(new_p)
    logger.info(f"🔔 New product added: {pid} @ promo {new_pr}")

    history = PriceHistory(product_id=pid, promo_price=new_pr, regular_price=new_reg)
    db.session.add(history)
    logger.info(f"✅ Polled prices at {datetime.utcnow().isoformat()}")
    db.session.commit()
    return {"alert": True, "new_price": new_pr}


@products_bp.route('/product/watch', methods=['POST'])
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


@products_bp.route('/products', methods=['GET'])
def list_products():
    prods = Product.query.all()
    result = []
    for p in prods:
        result.append({
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "regular_price": p.regular_price,
            "promo_price": p.promo_price,
            "stock_level": p.stock_level,
            "temperature_sensitive": p.temperature_sensitive,
        })
    return jsonify(result), 200


@products_bp.route('/product/<product_id>/history', methods=['GET'])
def get_price_history(product_id):
    history = (
        PriceHistory.query.filter_by(product_id=product_id)
        .order_by(PriceHistory.timestamp.desc())
        .all()
    )
    return jsonify([
        {
            "timestamp": h.timestamp.isoformat(),
            "promo_price": h.promo_price,
            "regular_price": h.regular_price,
        }
        for h in history
    ])


def monitor_watched_products(app):
    with app.app_context():
        token = get_access_token()
        loc = fetch_nearest_location(token, zip_code="45202")
        loc_id = loc.get("locationId")
        if not loc_id:
            logger.warning("⚠️  No Kroger location found")
            return
        for pid in WATCHED_IDS:
            items = fetch_products(token, term=pid, limit=5, location_id=loc_id)
            raw = next((i for i in items if i.get("productId") == pid), None)
            if not raw:
                logger.warning(f"⚠️  No data for {pid}")
                continue
            prod_data = map_kroger_to_zenday(raw)
            process_product_data(prod_data)
