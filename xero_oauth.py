from flask import Flask, redirect, request, jsonify
import os, base64, requests, urllib.parse, json, time
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("XERO_CLIENT_ID")
CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("XERO_REDIRECT_URI")
SCOPES = os.getenv("XERO_SCOPES", "openid profile email accounting.transactions offline_access")

AUTH_URL = "https://login.xero.com/identity/connect/authorize"
TOKEN_URL = "https://identity.xero.com/connect/token"
CONNECTIONS_URL = "https://api.xero.com/connections"

TOKENS_FILE = "xero_tokens.json"

app = Flask(__name__)

STATE = "demo-state-123"
TENANT_ID = None

# -------------------- Token Helpers --------------------

def basic_auth_header(client_id, client_secret):
    b = f"{client_id}:{client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(b).decode("utf-8")

def save_tokens(tokens: dict, tenant_id: str = None):
    data = {
        "tokens": tokens,
        "tenant_id": tenant_id,
        "obtained_at": int(time.time())
    }
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

    expires_in = tokens.get("expires_in", 0)
    obtained_at = tokens.get("obtained_at", 0)
    now = int(time.time())

    if now > obtained_at + expires_in - 60:
        print("🔄 Refreshing access token...")
        headers = {
            "Authorization": basic_auth_header(CLIENT_ID, CLIENT_SECRET),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        }
        resp = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
        if resp.status_code != 200:
            print("❌ Failed to refresh:", resp.text)
            return None, tenant_id
        tokens = resp.json()
        save_tokens(tokens, tenant_id)

    return tokens["access_token"], tenant_id


# -------------------- Routes --------------------

@app.route("/")
def home():
    return "Xero OAuth demo. Visit /xero/connect to start."

@app.route("/xero/connect")
def xero_connect():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": STATE,
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(url)

@app.route("/xero/callback")
def xero_callback():
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

    # ✅ Save both tokens + tenantId to disk
    save_tokens(TOKENS, tenant_id)

    return jsonify({
        "connected": True,
        "tenant_id": tenant_id,
        "tokens_saved": True
    })


@app.route("/xero/invoices")
def xero_invoices():
    """Fetch invoices (first 10)."""
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        return "Not connected. Visit /xero/connect first.", 400

    url = "https://api.xero.com/api.xro/2.0/Invoices"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
    }
    params = {"page": 1}
    r = requests.get(url, headers=headers, params=params, timeout=30)
    return jsonify(r.json()), r.status_code

# curl -X POST http://localhost:3000/xero/create_invoice \
#   -H "Content-Type: application/json" \
#   -d '{}'
@app.route("/xero/create_invoice", methods=["POST"])
def create_invoice():
    tokens, tenant_id = load_tokens()
    if not tokens or not tenant_id:
        return "❌ Not connected. Visit /xero/connect first.", 400

    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        return "❌ Missing access token or tenant ID.", 400

    url = "https://api.xero.com/api.xro/2.0/Invoices"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    invoice_body = {
        "Invoices": [
                        {
            "Type": "ACCREC",
            "Contact": {
                "Name": "Test Customer"
            },
            "LineItems": [
                {
                    "Description": "Deposit payment",
                    "Quantity": 1,
                    "UnitAmount": 11.00,
                    "AccountCode": "261",
                    # "TaxType": "TAX001"
                }
            ],
            "Date": "2025-10-01",
            "DueDate": "2025-10-15",
            # "InvoiceNumber": "DEP-3148586",
            "Status": "AUTHORISED"
            }
        ]
    }

    r = requests.post(url, headers=headers, json=invoice_body, timeout=30)
    if r.status_code != 200:
        return jsonify({"error": r.status_code, "body": r.text}), 400

    return jsonify(r.json()), 200

@app.route("/xero/accounts")
def xero_accounts():
    access_token, tenant_id= get_valid_access_token()
    if not access_token or not tenant_id:
        return "Not connected. Visit /xero/connect first.", 400

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
    }

    url = "https://api.xero.com/api.xro/2.0/Accounts"


    resp = requests.get(url, headers=headers, timeout=30)
    print(resp.status_code, resp.text)

    if resp.status_code != 200:
        return jsonify({"error": resp.status_code, "body": resp.text}), 400

    accounts = resp.json().get("Accounts", [])
    # Optional: filter only for your code 261
    filtered = [a for a in accounts if a.get("Code") == "261"]

    return jsonify(filtered if filtered else accounts), 200


@app.route("/xero/customer/<contact_id>")
def xero_customer(contact_id):
    """Fetch one customer by ContactID."""
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        return "Not connected. Visit /xero/connect first.", 400

    url = f"https://api.xero.com/api.xro/2.0/Contacts/{contact_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
    }

    resp = requests.get(url, headers=headers, timeout=30)

    if resp.status_code != 200:
        return jsonify({"error": resp.status_code, "body": resp.text}), 400

    return jsonify(resp.json().get("Contacts", [])), 200

@app.route("/xero/customers")
def xero_customers():
    """Fetch first 5 contacts (customers) from Xero."""
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        return "Not connected. Visit /xero/connect first.", 400

    url = "https://api.xero.com/api.xro/2.0/Contacts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
    }

    resp = requests.get(url, headers=headers, params={"page": 1}, timeout=30)

    if resp.status_code != 200:
        return jsonify({"error": resp.status_code, "body": resp.text}), 400

    contacts = resp.json().get("Contacts", [])

    # Just return first 5 for testing
    return jsonify(contacts[:5]), 200

@app.route("/xero/create_customer", methods=["POST"])
def create_customer():
    """Create a fake customer in Xero only if they don't already exist."""
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        return "Not connected. Visit /xero/connect first.", 400

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Fake customer info
    first_name = "Testy"
    last_name = "McTester"
    email = "fake.customer@example.com"

    # 1️⃣ Check if customer already exists by email
    url_check = "https://api.xero.com/api.xro/2.0/Contacts"
    params = {"where": f'EmailAddress=="{email}"'}
    resp_check = requests.get(url_check, headers=headers, params=params, timeout=30)

    if resp_check.status_code == 200:
        contacts = resp_check.json().get("Contacts", [])
        if contacts:
            print("✅ Customer already exists in Xero:", contacts[0]["Name"])
            return jsonify({"status": "exists", "contact": contacts[0]}), 200

    # 2️⃣ Otherwise, create the new fake customer
    url_create = "https://api.xero.com/api.xro/2.0/Contacts"
    payload = {
        "Contacts": [
            {
                "Name": f"{first_name} {last_name}",
                "FirstName": first_name,
                "LastName": last_name,
                "EmailAddress": email,
                "Phones": [{"PhoneType": "MOBILE", "PhoneNumber": "123456789"}]
            }
        ]
    }

    resp_create = requests.post(url_create, headers=headers, json=payload, timeout=30)
    print("➕ Creating customer:", resp_create.status_code, resp_create.text)

    if resp_create.status_code not in (200, 201):
        return jsonify({"error": resp_create.status_code, "body": resp_create.text}), 400

    return jsonify({"status": "created", "contact": resp_create.json().get("Contacts", [])[0]}), 201


# -------------------- Run --------------------

if __name__ == "__main__":
    app.run(host="localhost", port=3000, debug=True)

