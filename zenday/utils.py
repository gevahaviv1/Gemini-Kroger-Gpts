import json


def save_token(token: str, path: str = 'token.json'):
    with open(path, 'w') as f:
        json.dump({'token': token, 'access_token': token}, f)


def get_saved_token(path: str = 'token.json'):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            return data.get('access_token') or data.get('token')
    except (FileNotFoundError, json.JSONDecodeError):
        return None
