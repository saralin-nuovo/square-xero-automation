import os
from dotenv import load_dotenv
from square.environment import SquareEnvironment

load_dotenv()

CLIENT_ID = os.getenv("XERO_CLIENT_ID")
CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("XERO_REDIRECT_URI")
SCOPES = os.getenv("XERO_SCOPES")

AUTH_URL = "https://login.xero.com/identity/connect/authorize"
TOKEN_URL = "https://identity.xero.com/connect/token"
CONNECTIONS_URL = "https://api.xero.com/connections"
TOKENS_FILE = "xero_tokens.json"

SQUARE_ENV = SquareEnvironment.SANDBOX

if SQUARE_ENV is SquareEnvironment.PRODUCTION:
    SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_PROD_ACCESS_TOKEN")
    SQUARE_LOCATION_ID = os.getenv("SQUARE_PROD_LOCATION_ID")
elif SQUARE_ENV is SquareEnvironment.SANDBOX:
    SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_SANDBOX_ACCESS_TOKEN")
    SQUARE_LOCATION_ID = os.getenv("SQUARE_SANDBOX_LOCATION_ID")
else:
    raise RuntimeError(f"Unsupported SQUARE_ENV: {SQUARE_ENV}")

XERO_ACCOUNT_CODES = {
    "beauty": "261",
    "collections": "260",
}