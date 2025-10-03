# routes/auth_routes.py
from flask import Blueprint, jsonify, request, redirect
import requests, urllib.parse
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES, AUTH_URL, TOKEN_URL, CONNECTIONS_URL
from utils.auth import basic_auth_header
from services.token_service import save_tokens

auth_bp = Blueprint("auth", __name__)

STATE = "demo-state-123"

@auth_bp.route("/xero/connect")
def xero_connect():
    """Redirect user to Xero login/consent screen."""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": STATE,
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(url)


@auth_bp.route("/xero/callback")
def xero_callback():
    """Handle Xero OAuth2 callback and save tokens + tenant."""
    if request.args.get("state") != STATE:
        return "State mismatch.", 400

    code = request.args.get("code")
    if not code:
        return "Missing code.", 400

    # Exchange code -> tokens
    headers = {
        "Authorization": basic_auth_header(CLIENT_ID, CLIENT_SECRET),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    tok = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
    if tok.status_code != 200:
        return jsonify({"token_error": tok.status_code, "body": tok.text}), 400

    TOKENS = tok.json()

    # ✅ Fetch tenants
    con = requests.get(
        CONNECTIONS_URL,
        headers={"Authorization": f"Bearer {TOKENS['access_token']}"},
        timeout=30,
    )
    if con.status_code != 200:
        return jsonify({"connections_error": con.status_code, "body": con.text}), 400

    conns = con.json()
    if not conns:
        return "❌ No tenant connections found.", 400

    tenant_id = conns[0]["tenantId"]

    # ✅ Save both tokens + tenantId
    save_tokens(TOKENS, tenant_id)

    return jsonify({
        "connected": True,
        "tenant_id": tenant_id,
        "tokens_saved": True
    })
