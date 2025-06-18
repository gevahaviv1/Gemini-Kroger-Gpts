import os
import json
from flask import Flask, request, jsonify, session, redirect
from db.models import db, Product, PriceHistory
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone

# Simple token storage
def save_token(token):
    with open('token.json', 'w') as f:
        json.dump({'token': token, 'access_token': token}, f)
    return token

def get_saved_token():
    try:
        with open('token.json', 'r') as f:
            data = json.load(f)
            # Try both keys for backward compatibility
            return data.get('access_token') or data.get('token')
    except (FileNotFoundError, json.JSONDecodeError):
        return None

from scripts.fetch_kroger_data import (
    fetch_products,
    get_access_token,
    fetch_nearest_location,
)
from scripts.kroger_cart import get_cart, create_cart, add_to_cart, remove_from_cart
from map_kroger_data.mapper import map_kroger_to_zenday

scheduler = BackgroundScheduler()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///zenday.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")  # Use env var or fallback
    
    # Improve session configuration
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = 1800  # 30 minutes
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return "Zenday Alert Service Running"

        # 1) kick off the Authorization Code flow

    # top-of-file
    WATCHED_IDS = ["0001111041700"]
    POLL_INTERVAL_MINUTES = 10

    def process_product_data(prod_data):
        """
        Given a mapped product dict, upsert into DB and
        print an alert if it’s new or the promo price dropped.
        Returns a dict with the result.
        """
        pid = prod_data["id"]
        new_reg = prod_data["price"]["regular"]
        new_pr = prod_data["price"]["promo"]

        existing = db.session.get(Product, pid)

        if existing:
            old_pr = existing.promo_price or 0
            new_pr = old_pr - 0.1

            if new_pr is not None and new_pr < old_pr:
                # Update price in the database
                existing.regular_price = new_reg
                existing.promo_price = new_pr
                db.session.add(existing)
                history = PriceHistory(
                    product_id=pid, promo_price=new_pr, regular_price=new_reg
                )
                db.session.add(history)
                print(f"✅ Polled prices at {datetime.now(timezone.utc).isoformat()}")
                db.session.commit()
                print(f"🔔 Price drop for {pid}: {old_pr} → {new_pr}")
                return {"alert": True, "old_price": old_pr, "new_price": new_pr}
                # Record the price drop

            history = PriceHistory(
                product_id=pid, promo_price=new_pr, regular_price=new_reg
            )
            db.session.add(history)
            print(f"✅ Polled prices at {datetime.now(timezone.utc).isoformat()}")
            db.session.commit()
            return {"alert": False}

        # not exists → create + alert
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
        print(f"🔔 New product added: {pid} @ promo {new_pr}")

        # Record the price drop
        history = PriceHistory(
            product_id=pid, promo_price=new_pr, regular_price=new_reg
        )
        db.session.add(history)
        print(f"✅ Polled prices at {datetime.now(timezone.utc).isoformat()}")
        db.session.commit()
        return {"alert": True, "new_price": new_pr}

    def monitor_watched_products():
        with app.app_context():
            token = get_access_token()

            loc = fetch_nearest_location(token, zip_code="45202")
            loc_id = loc.get("locationId")
            if not loc_id:
                print("⚠️  No Kroger location found")
                return

            for pid in WATCHED_IDS:
                items = fetch_products(token, term=pid, limit=5, location_id=loc_id)
                raw = next((i for i in items if i.get("productId") == pid), None)
                if not raw:
                    print(f"⚠️  No data for {pid}")
                    continue
                prod_data = map_kroger_to_zenday(raw)
                process_product_data(prod_data)

    # schedule inside create_app() just before `return app`
    scheduler.add_job(
        func=monitor_watched_products,
        trigger="interval",
        minutes=POLL_INTERVAL_MINUTES,
        id="kroger_watchlist_job",
        replace_existing=True,
    )

    # Route to manually trigger for one product
    @app.route("/product/watch", methods=["POST"])
    def upsert_product_and_alert():
        token = app.config.get("KROGER_TOKEN")
        if not token:
            return jsonify({"error": "Not authorized – please /login"}), 401

        data = request.get_json() or {}
        prod_data = data.get("product")
        if not prod_data:
            return jsonify({"error": "Missing 'product' object"}), 400

        id = prod_data.get("id")
        if not id:
            return jsonify({"error": "Missing product_id"}), 400

        result = process_product_data(prod_data)
        return jsonify(result), 200

    @app.route("/products", methods=["GET"])
    def list_products():
        prods = Product.query.all()
        # turn each SQLAlchemy object into a plain dict
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
                    # … include any other fields you care about …
                }
            )
        return jsonify(result), 200

    @app.route("/product/<product_id>/history", methods=["GET"])
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

    # Cart management endpoints
    @app.route("/auth/login")
    def auth_login():
        """Start OAuth2 Authorization Code flow for cart access."""
        authorize_url = "https://api.kroger.com/v1/connect/oauth2/authorize"
        params = {
            "client_id": os.getenv("KROGER_CLIENT_ID"),
            "response_type": "code",
            "redirect_uri": os.getenv("REDIRECT_URI", "http://localhost:5000/auth/callback"),
            "scope": "cart:read cart:write product.compact profile.compact",
        }
        auth_url = f"{authorize_url}?" + "&".join(f"{k}={v}" for k, v in params.items())
        return jsonify({"auth_url": auth_url})

    @app.route("/callback")
    def callback_redirect():
        """Redirect from /callback to /auth/callback with the same query parameters"""
        # This helps when the OAuth redirect_uri is set to /callback but our app expects /auth/callback
        return redirect(f"/auth/callback?{request.query_string.decode()}", code=307)
        
    @app.route("/auth/callback")
    def auth_callback():
        """Handle OAuth2 callback and get access token."""
        code = request.args.get("code")
        if not code:
            return jsonify({"error": "No authorization code received"}), 400

        try:
            # Get token with full debugging
            print("\n--- DEBUG: Getting access token ---")
            print(f"Authorization code: {code[:10]}...")
            full_token_response = get_access_token(auth_code=code, return_full_response=True)
            
            # Log the full token response for debugging
            print(f"\n--- DEBUG: Full token response ---")
            print(f"Response: {json.dumps(full_token_response, indent=2)}")
            
            # Extract the token
            token = full_token_response.get('access_token')
            if not token:
                raise ValueError("No access_token in response")
                
            print(f"✅ Auth success! Token received: {token[:10]}...")
            
            # Store in both session and file for reliability
            session['kroger_token'] = token
            session.modified = True
            
            # Store the full response for debugging
            with open('token_full.json', 'w') as f:
                json.dump(full_token_response, f, indent=2)
            
            # Also store in file
            save_token(token)
            print(f"✅ Saved token to file and session")
            
            # Return the response
            return jsonify({
                "message": "Successfully authenticated", 
                "token_start": token[:10] if token else None,
                "full_response": full_token_response
            })
        except Exception as e:
            print(f"❌ Auth error: {str(e)}")
            return jsonify({"error": str(e)}), 401

    @app.route("/cart", methods=["GET"])
    def view_cart():
        # Try to get token from session first, then from file
        token = session.get('kroger_token') or get_saved_token()
        print(f"🔍 /cart: Session keys: {list(session.keys())}")
        print(f"🔍 /cart: Token available: {'Yes' if token else 'No'}")
        if not token:
            return jsonify({"error": "Please authenticate first at /auth/login"}), 401

        try:
            # Use the OAuth token directly to get the cart
            # The API will return the customer's default cart
            cart = get_cart(token)
            return jsonify(cart), 200
        except Exception as e:
            print(f"Cart error: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/cart/add", methods=["POST"])
    def add_item_to_cart():
        # Try to get token from session first, then from file
        token = session.get('kroger_token') or get_saved_token()
        print(f"🔍 /cart/add: Session keys: {list(session.keys())}")
        print(f"🔍 /cart/add: Token available: {'Yes' if token else 'No'}")
        if not token:
            return jsonify({"error": "Please authenticate first at /auth/login"}), 401

        data = request.get_json()
        if not data or "product_id" not in data:
            return jsonify({"error": "Missing product_id"}), 400

        quantity = data.get("quantity", 1)
        allow_substitutes = data.get("allow_substitutes", True)
        special_instructions = data.get("special_instructions", "")

        try:
            # First try to get the current cart
            try:
                print("Getting current cart...")
                cart_response = get_cart(token)
                # Get the cart ID from the response
                cart_id = None
                if 'data' in cart_response and len(cart_response['data']) > 0:
                    cart_id = cart_response['data'][0]['id']
                    print(f"Existing cart found with ID: {cart_id}")
            except Exception as e:
                print(f"No existing cart found or error: {str(e)}")
                cart_id = None
            
            # Prepare item data
            item_data = {
                "upc": data["product_id"],
                "quantity": quantity,
                "allowSubstitutes": allow_substitutes
            }
            
            if special_instructions:
                item_data["specialInstructions"] = special_instructions
            
            # If we have a cart ID, add to existing cart, otherwise create a new one
            if cart_id:
                print(f"Adding item to existing cart {cart_id}...")
                result = add_to_cart(token, cart_id, [item_data])
                return jsonify(result), 200
            else:
                print("Creating new cart with item...")
                result = create_cart(token, [item_data])
                return jsonify(result), 201
        except Exception as e:
            print(f"Cart error: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
    @app.route("/cart/remove", methods=["DELETE"])
    def remove_item_from_cart():
        # Try to get token from session first, then from file
        token = session.get('kroger_token') or get_saved_token()
        print(f"🔍 /cart/remove: Token available: {'Yes' if token else 'No'}")
        if not token:
            return jsonify({"error": "Please authenticate first at /auth/login"}), 401

        data = request.get_json()
        if not data or "product_id" not in data:
            return jsonify({"error": "Missing product_id"}), 400

        try:
            # First try to get the current cart
            try:
                print("Getting current cart...")
                cart_response = get_cart(token)
                # Get the cart ID from the response
                if 'data' in cart_response and len(cart_response['data']) > 0:
                    cart_id = cart_response['data'][0]['id']
                    print(f"Existing cart found with ID: {cart_id}")
                else:
                    return jsonify({"error": "No cart found"}), 404
            except Exception as e:
                print(f"Error getting cart: {str(e)}")
                return jsonify({"error": "No cart found"}), 404
            
            # Remove the item from the cart
            product_id = data["product_id"]
            print(f"Removing item {product_id} from cart {cart_id}...")
            result = remove_from_cart(token, cart_id, product_id)
            return jsonify(result), 200
        except Exception as e:
            print(f"Cart error: {str(e)}")
            return jsonify({"error": str(e)}), 500

    return app


if __name__ == "__main__":
    app = create_app()

    # Only start the scheduler if this is the main process (not the reloader)
    from werkzeug.serving import is_running_from_reloader

    if not is_running_from_reloader():
        print("Starting background scheduler...")
        scheduler.start()

    # Run with explicit session support
    app.run(debug=True, host='127.0.0.1', port=5000)
