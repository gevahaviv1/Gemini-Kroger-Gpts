import os
import json
import logging
from flask import Blueprint, jsonify, request, redirect, session
from ..services.cart import get_cart, add_to_cart, remove_from_cart
from ..services.kroger_api import get_access_token
from ..utils import save_token, get_saved_token

logger = logging.getLogger(__name__)

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/auth/login")
def auth_login():
    authorize_url = "https://api.kroger.com/v1/connect/oauth2/authorize"
    params = {
        "client_id": os.getenv("KROGER_CLIENT_ID"),
        "response_type": "code",
        "redirect_uri": os.getenv(
            "REDIRECT_URI", "http://localhost:5000/auth/callback"
        ),
        "scope": "cart.basic:write",
    }
    auth_url = f"{authorize_url}?" + "&".join(f"{k}={v}" for k, v in params.items())
    return jsonify({"auth_url": auth_url})


@cart_bp.route("/callback")
def callback_redirect():
    return redirect(f"/auth/callback?{request.query_string.decode()}", code=307)


@cart_bp.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No authorization code received"}), 400
    try:
        full_token_response = get_access_token(
            auth_code=code, return_full_response=True
        )
        token = full_token_response.get("access_token")
        if not token:
            raise ValueError("No access_token in response")

        logger.info(f"✅ Auth success! Token received.")
        session["kroger_token"] = token
        session.modified = True
        with open("token_full.json", "w") as f:
            json.dump(full_token_response, f, indent=2)
        save_token(token)
        logger.info("✅ Saved token to file and session")
        return jsonify(
            {
                "message": "Successfully authenticated",
            }
        )
    except Exception as e:
        logger.error(f"❌ Auth error: {str(e)}")
        return jsonify({"error": str(e)}), 401


@cart_bp.route("/cart", methods=["GET"])
def view_cart():
    token = session.get("kroger_token") or get_saved_token()
    if not token:
        return jsonify({"error": "Please authenticate first at /auth/login"}), 401
    try:
        cart = get_cart(token)
        return jsonify(cart), 200
    except Exception as e:
        logger.error(f"Cart error: {str(e)}")
        return jsonify({"Cart error": str(e)})


@cart_bp.route("/cart/add", methods=["PUT"])
def add_item_to_cart():
    token = session.get("kroger_token") or get_saved_token()

    if not token:
        return jsonify({"error": "Please authenticate first at /auth/login"}), 401

    data = request.get_json()
    if not data or "upc" not in data:
        return jsonify({"error": "Missing upc"}), 400

    # quantity = data.get("quantity", 1)
    # modality = data.get("modality", "PICKUP")
    # item_data = {"upc": data["upc"], "quantity": quantity, "modality": modality}

    try:
        logger.info(f"Adding item to cart.")
        result = add_to_cart(token, data)
        logger.info("✅ Item added to cart")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Cart error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@cart_bp.route("/cart/remove", methods=["DELETE"])
def remove_item_from_cart():
    token = session.get("kroger_token") or get_saved_token()
    logger.info(f"🔍 /cart/remove: Token available: {'Yes' if token else 'No'}")

    if not token:
        return jsonify({"error": "Please authenticate first at /auth/login"}), 401

    data = request.get_json()
    if not data or "product_id" not in data:
        return jsonify({"error": "Missing product_id"}), 400

    try:
        try:
            logger.info("Getting current cart...")
            cart_response = get_cart(token)
            if "data" in cart_response and len(cart_response["data"]) > 0:
                cart_id = cart_response["data"][0]["id"]
                logger.info(f"Existing cart found with ID: {cart_id}")
            else:
                return jsonify({"error": "No cart found"}), 404
        except Exception as e:
            logger.error(f"Error getting cart: {str(e)}")
            return jsonify({"error": "No cart found"}), 404
        product_id = data["product_id"]
        logger.info(f"Removing item {product_id} from cart {cart_id}...")
        result = remove_from_cart(token, cart_id, product_id)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Cart error: {str(e)}")
        return jsonify({"error": str(e)}), 500
