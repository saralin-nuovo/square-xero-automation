# services/xero_service.py
from services.token_service import get_valid_access_token, load_tokens
from utils.http import safe_get, safe_post
import requests 
import os
from datetime import date

from config import XERO_ACCOUNT_CODES 

BASE_URL = "https://api.xero.com/api.xro/2.0"

def get_headers(access_token, tenant_id, json=False):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
    }
    if json:
        headers["Content-Type"] = "application/json"
    return headers


def fetch_invoices(page=1):
    """Fetch invoices from Xero (paginated)."""
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        return None, {"error": "not_connected", "message": "Visit /xero/connect first"}, 400

    url = f"{BASE_URL}/Invoices"
    headers = get_headers(access_token, tenant_id)
    return safe_get(url, headers=headers, params={"page": page})


def create_invoice(invoice_body):
    """Create an invoice in Xero."""
    tokens, tenant_id = load_tokens()
    if not tokens or not tenant_id:
        return None, {"error": "not_connected", "message": "Visit /xero/connect first"}, 400

    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        return None, {"error": "auth_failed", "message": "Missing access token or tenant ID"}, 400

    url = f"{BASE_URL}/Invoices"
    headers = get_headers(access_token, tenant_id, json=True)
    return safe_post(url, headers=headers, json=invoice_body)


def fetch_contacts(limit=5):
    """Fetch first N contacts from Xero."""
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        return None, {"error": "not_connected", "message": "Visit /xero/connect first"}, 400

    url = f"{BASE_URL}/Contacts"
    headers = get_headers(access_token, tenant_id)
    data, error, status = safe_get(url, headers=headers, params={"page": 1})
    if error:
        return None, error, status
    return data.get("Contacts", [])[:limit], None, 200


def create_contact(contact_payload):
    """Create a contact in Xero (idempotent — you can check before inserting)."""
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        return None, {"error": "not_connected", "message": "Visit /xero/connect first"}, 400

    url = f"{BASE_URL}/Contacts"
    headers = get_headers(access_token, tenant_id, json=True)
    return safe_post(url, headers=headers, json=contact_payload)


XERO_CONTACTS_URL = "https://api.xero.com/api.xro/2.0/Contacts"

def _where(q: str): return {"where": q}
def _digits_only(s: str) -> str: return "".join(ch for ch in (s or "") if ch.isdigit())
# services/xero_service.py
import requests
from services.token_service import get_valid_access_token

XERO_CONTACTS_URL = "https://api.xero.com/api.xro/2.0/Contacts"

def _where(q: str): return {"where": q}
def _digits_only(s: str) -> str: return "".join(ch for ch in (s or "") if ch.isdigit())

def find_or_create_contact_from_square(cust):
    """
    Match priority (no name matching):
      1) AccountNumber == <square_id>      # Zapier-style (no SQ- prefix)
      2) EmailAddress == email
    Also checks legacy 'SQ-<square_id>' on read for backward compat,
    but writes AccountNumber as <square_id> only.
    """
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        raise RuntimeError("Not connected to Xero. Run the Xero OAuth flow first.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    square_id = getattr(cust, "id", "") or ""
    given     = getattr(cust, "given_name", "") or ""
    family    = getattr(cust, "family_name", "") or ""
    email     = getattr(cust, "email_address", "") or ""
    phone     = getattr(cust, "phone_number", "") or ""

    # Zapier-style account number (no prefix)
    account_number = square_id or None
    legacy_account_number = f"SQ-{square_id}" if square_id else None  # read-only check

    # 1) Match by AccountNumber (raw Square ID)
    if account_number:
        r = requests.get(XERO_CONTACTS_URL, headers=headers, params=_where(f'AccountNumber=="{account_number}"'), timeout=30)
        if r.status_code == 200 and r.json().get("Contacts"):
            return r.json()["Contacts"][0], False

        # 1b) Backward-compat: match legacy 'SQ-<id>' if present
        if legacy_account_number:
            r2 = requests.get(XERO_CONTACTS_URL, headers=headers, params=_where(f'AccountNumber=="{legacy_account_number}"'), timeout=30)
            if r2.status_code == 200 and r2.json().get("Contacts"):
                contact = r2.json()["Contacts"][0]
                # Optional: normalize to raw id going forward
                patch_payload = {"Contacts": [{"ContactID": contact.get("ContactID"), "AccountNumber": account_number}]}
                try:
                    _ = requests.post(XERO_CONTACTS_URL, headers=headers, json=patch_payload, timeout=30)
                except Exception:
                    pass
                return contact, False

    # 2) Fallback: match by EmailAddress
    if email:
        r = requests.get(XERO_CONTACTS_URL, headers=headers, params=_where(f'EmailAddress=="{email}"'), timeout=30)
        if r.status_code == 200 and r.json().get("Contacts"):
            contact = r.json()["Contacts"][0]
            # Backfill AccountNumber (raw id) if missing or legacy
            if account_number:
                if not contact.get("AccountNumber") or contact.get("AccountNumber") == legacy_account_number:
                    patch_payload = {"Contacts": [{"ContactID": contact.get("ContactID"), "AccountNumber": account_number}]}
                    try:
                        _ = requests.post(XERO_CONTACTS_URL, headers=headers, json=patch_payload, timeout=30)
                    except Exception:
                        pass
            return contact, False

    # --- Create new contact (Name is required by Xero; use email when available) ---
    name_for_xero = email if email else f"Square [{square_id or 'no-id'}]"
    payload = {
        "Contacts": [
            {
                "Name": name_for_xero,                 # we do NOT use Name for matching
                "FirstName": given or None,
                "LastName": family or None,
                "EmailAddress": email or None,
                "AccountNumber": account_number or None,   # <-- raw Square ID (Zapier-style)
                "Phones": (
                    [{"PhoneType": "MOBILE", "PhoneNumber": _digits_only(phone)[:50]}]
                    if phone else []
                ),
            }
        ]
    }

    create = requests.post(XERO_CONTACTS_URL, headers=headers, json=payload, timeout=30)
    if create.status_code not in (200, 201):
        raise RuntimeError(f"Xero contact create failed: {create.status_code} {create.text}")

    return create.json().get("Contacts", [None])[0], True

XERO_INVOICES_URL = "https://api.xero.com/api.xro/2.0/Invoices"

def create_xero_invoice(contact_id: str, items: list, square_order_id: str, reference: str | None = None):
    """
    Create an invoice in Xero from Square order data.

    Args:
      contact_id: Xero ContactID to assign invoice to
      items: list of dicts like:
        {"description": str, "quantity": int, "unit_amount": float}
      square_order_id: The Square order ID (used in invoice number)

    Returns:
      Xero API response JSON
    """
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        raise RuntimeError("Not connected to Xero. Run the OAuth connect flow first.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    line_items = []
    for it in items:
        desc = it["description"].lower()
        # Pick account code based on keywords
        account_code = "200"
        for keyword, code in XERO_ACCOUNT_CODES.items():
            if keyword in desc:
                account_code = code
                break
        li = {
            "Description": it["var_name"],
            "Quantity": int(it["quantity"]),
            "UnitAmount": float(it["unit_amount"]),
            "AccountCode": account_code,
        }
        line_items.append(li)

    today_str = date.today().isoformat()

    payload = {
        "Invoices": [{
            "Type": "ACCREC",
            "Contact": {"ContactID": contact_id},
            "LineItems": line_items,
            "InvoiceNumber": f"SQUARE - {square_order_id}",
            "Date": today_str,      # Issue date
            "DueDate": today_str,   # Same day due
            "Status": "AUTHORISED", # currently SUBMITTED AUTHORISED
            "LineAmountTypes": "Inclusive", # 👈 tax inclusive
        }]
    }
    if reference:
        payload["Invoices"][0]["Reference"] = reference


    resp = requests.post(XERO_INVOICES_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Xero invoice create failed: {resp.status_code} {resp.text}")
    return resp.json()

def update_xero_invoice_reference(invoice_id: str, reference: str):
    """
    Update an existing Xero invoice with a new reference string.
    """
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        raise RuntimeError("Not connected to Xero. Run the OAuth connect flow first.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "Invoices": [{
            "InvoiceID": invoice_id,
            "Reference": reference,
        }]
    }

    # 👉 Use POST not PUT, and no /{invoice_id} in URL
    resp = requests.post(XERO_INVOICES_URL, headers=headers, json=payload, timeout=30)

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Xero invoice update failed: {resp.status_code} {resp.text}")

    return resp.json()


def get_xero_invoice_by_order_id(square_order_id: str):
    access_token, tenant_id = get_valid_access_token()
    if not access_token or not tenant_id:
        raise RuntimeError("Not connected to Xero")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
    }

    invoice_number = f"SQUARE - {square_order_id}"
    url = f"{XERO_INVOICES_URL}?InvoiceNumbers={invoice_number}"

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Xero invoice lookup failed: {resp.status_code} {resp.text}")

    data = resp.json()
    invoices = data.get("Invoices", [])
    return invoices[0] if invoices else None
