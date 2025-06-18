import os
import logging
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")
TOKEN_URL = "https://api.kroger.com/v1/connect/oauth2/token"
PRODUCTS_URL = "https://api.kroger.com/v1/products"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_access_token(auth_code=None, return_full_response=False):
    """
    Get access token using either Client Credentials flow (for product API)
    or Authorization Code flow (for cart API).
    
    Args:
        auth_code: Optional authorization code from OAuth2 redirect
        return_full_response: If True, returns the full response JSON instead of just the token
    """
    if auth_code:
        # Authorization Code flow for cart operations
        payload = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": os.getenv("REDIRECT_URI", "http://localhost:5000/auth/callback")
            # Note: We're not setting scope here because it should be set during the initial authorization request
        }
        
        logger.info(f"Authorization Code payload: {payload}")
    else:
        # Client Credentials flow for product operations
        payload = {
            "grant_type": "client_credentials",
            "scope": "product.compact"
        }
    
    try:
        # Encode client ID and secret for Authorization header
        auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_b64}"
        }
        
        logger.info(f"Token request URL: {TOKEN_URL}")
        logger.info(f"Token request headers: {headers}")
        
        resp = requests.post(TOKEN_URL, headers=headers, data=payload)
        
        logger.info(f"Token response status: {resp.status_code}")
        try:
            logger.info(f"Token response body: {resp.text[:200]}...")
        except:
            logger.info("Could not print response body")
        
        if resp.status_code != 200:
            error_msg = f"Failed to get token. Status code: {resp.status_code}"
            try:
                error_details = resp.json()
                error_msg += f": {error_details}"
            except:
                error_msg += f": {resp.text}"
            logger.error(error_msg)
            resp.raise_for_status()
        
        response_data = resp.json()
        
        # If requested, return the full response
        if return_full_response:
            return response_data
            
        token = response_data.get("access_token")
        if not token:
            raise ValueError("No access_token in response")
        logger.info("Obtained access token successfully")
        return token
    except Exception as e:
        logger.error(f"Error obtaining token: {str(e)}")
        raise


def fetch_nearest_location(token: str, zip_code: str = "45202") -> dict:
    url = "https://api.kroger.com/v1/locations"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    params = {
        "filter.zipCode.near": zip_code,
        "filter.limit": 1,
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return data[0] if data else {}


def fetch_products(
    token: str, term: str, limit: int = 50, location_id: str = None
) -> list:
    """
    Fetch products from Kroger with pagination.
    Returns a list of product dicts.
    """
    headers = {"Authorization": f"Bearer {token}"}
    params = {"filter.term": term, "filter.limit": limit}

    if location_id:
        params["filter.locationId"] = location_id

    products = []
    next_url = PRODUCTS_URL

    while next_url:
        try:
            resp = requests.get(next_url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            page_items = data.get("data", [])
            products.extend(page_items)
            logger.info(f"Fetched {len(page_items)} items")

            # Parse Link header for next page
            link = resp.headers.get("Link", "")
            next_url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip()[1:-1]
                    break
            params = {}  # only needed on first request
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            break

    return products
