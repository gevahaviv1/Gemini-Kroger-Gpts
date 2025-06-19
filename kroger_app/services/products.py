import logging
from datetime import datetime
from ..models import Product, PriceHistory, db
from ..services.kroger_api import (
    get_access_token,
    fetch_nearest_location,
    fetch_products,
)

logger = logging.getLogger(__name__)


def map_kroger_to_zenday(data: dict) -> dict:
    item = data.get("items", [{}])[0]
    aisle = (data.get("aisleLocations") or [{}])[0]
    image = data.get("images", [{}])[0].get("sizes", [{}])[0]
    logger.info(item.get("price", {}).get("regular"))
    return {
        "id": data.get("productId"),
        "name": data.get("description"),
        "brand": data.get("brand"),
        "category": data.get("categories", [None])[0],
        "image_url": image.get("url"),
        "product_url": f"https://www.kroger.com{data.get('productPageURI')}",
        "price": {
            "regular": item.get("price", {}).get("regular"),
            "promo": item.get("price", {}).get("promo"),
        },
        "fulfillment": item.get("fulfillment", {}),
        "stock_level": item.get("inventory", {}).get("stockLevel"),
        "size": item.get("size"),
        "sold_by": item.get("soldBy"),
        "location": {
            "aisle": aisle.get("number"),
            "shelf": aisle.get("shelfNumber"),
            "bay": aisle.get("bayNumber"),
            "side": aisle.get("side"),
        },
        "dimensions": {
            "width": float(data.get("itemInformation", {}).get("width", 0)),
            "height": float(data.get("itemInformation", {}).get("height", 0)),
            "depth": float(data.get("itemInformation", {}).get("depth", 0)),
        },
        "temperature_sensitive": data.get("temperature", {}).get(
            "heatSensitive", False
        ),
    }


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
            history = PriceHistory(
                product_id=pid, promo_price=new_pr, regular_price=new_reg
            )
            db.session.add(history)
            logger.info(f"✅ Polled prices at {datetime.utcnow().isoformat()}")
            db.session.commit()
            logger.info(f"🔔 Price drop for {pid}: {old_pr} → {new_pr}")
            return {"alert": True, "old_price": old_pr, "new_price": new_pr}

        history = PriceHistory(
            product_id=pid, promo_price=new_pr, regular_price=new_reg
        )
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


def monitor_watched_products(app, watched_ids):
    with app.app_context():
        token = get_access_token()
        loc = fetch_nearest_location(token, zip_code="45202")
        loc_id = loc.get("locationId")
        if not loc_id:
            logger.warning("⚠️  No Kroger location found")
            return
        for pid in watched_ids:
            items = fetch_products(token, term=pid, limit=5, location_id=loc_id)
            raw = next((i for i in items if i.get("productId") == pid), None)
            if not raw:
                logger.warning(f"⚠️  No data for {pid}")
                continue
            prod_data = map_kroger_to_zenday(raw)
            process_product_data(prod_data)
