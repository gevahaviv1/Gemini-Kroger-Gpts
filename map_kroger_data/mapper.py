def map_kroger_to_zenday(data: dict) -> dict:
    item = data.get("items", [{}])[0]
    aisle = (data.get("aisleLocations") or [{}])[0]
    image = data.get("images", [{}])[0].get("sizes", [{}])[0]
    print(item.get("price", {}).get("regular"))
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
