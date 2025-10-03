import json, os, time, requests
from utils.auth import basic_auth_header
from config import CLIENT_ID, CLIENT_SECRET, TOKEN_URL, TOKENS_FILE

def save_tokens(tokens: dict, tenant_id: str = None):
    data = {"tokens": tokens, "tenant_id": tenant_id, "obtained_at": int(time.time())}
    with open(TOKENS_FILE, "w") as f:
        json.dump(data, f)

def load_tokens():
    if not os.path.exists(TOKENS_FILE):
        return None, None
    with open(TOKENS_FILE, "r") as f:
        data = json.load(f)
    return data.get("tokens"), data.get("tenant_id")

def get_valid_access_token():
    tokens, tenant_id = load_tokens()
    if not tokens:
        return None, None

    now = int(time.time())
    if now > tokens.get("obtained_at", 0) + tokens.get("expires_in", 0) - 60:
        headers = {
            "Authorization": basic_auth_header(CLIENT_ID, CLIENT_SECRET),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]}
        resp = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
        if resp.status_code != 200:
            return None, tenant_id
        tokens = resp.json()
        save_tokens(tokens, tenant_id)

    return tokens["access_token"], tenant_id
