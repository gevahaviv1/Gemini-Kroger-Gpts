import json
import logging

logger = logging.getLogger(__name__)


def save_token(token: str, path: str = "token.json"):
    with open(path, "w") as f:
        json.dump({"token": token, "access_token": token}, f)


def get_saved_token(path: str = "token.json"):
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("token")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def exithandle_kroger_api_response(
    response, success_status_code=200, success_message=""
):
    if response.status_code == success_status_code:
        return {"success": True, "message": success_message}
    elif response.status_code == 401:
        raise Exception(
            "Unauthorized: Please check your API credentials and ensure you have cart access"
        )
    elif response.status_code == 403:
        raise Exception(
            "Forbidden: Your token doesn't have the required cart.basic scope"
        )
    else:
        raise Exception(f"Cart API error: {response.status_code} - {response.text}")


def handle_kroger_request_exception(e):
    logger.error(f"Exception: {str(e)}")
    if hasattr(e, "response") and e.response is not None:
        if e.response.status_code == 401:
            raise Exception(
                "Unauthorized: Please check your API credentials and ensure you have cart access"
            )
        elif e.response.status_code == 403:
            raise Exception(
                "Forbidden: Your token doesn't have the required cart.basic scope"
            )
        elif e.response.status_code == 400:
            raise Exception(
                f"Bad request: {e.response.json().get('reason', 'Unknown error')}"
            )
        elif e.response.status_code == 404:
            raise Exception("Cart not found")
    raise Exception(f"Cart API error: {str(e)}")
