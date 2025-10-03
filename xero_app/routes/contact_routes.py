# routes/contact_routes.py
from flask import Blueprint, jsonify, request
from services.xero_service import fetch_contacts, create_contact

contact_bp = Blueprint("contact", __name__)

@contact_bp.route("/xero/customers")
def xero_customers():
    """Fetch first 5 contacts (customers)."""
    contacts, error, status = fetch_contacts(limit=5)
    if error:
        return jsonify(error), status
    return jsonify(contacts), status


@contact_bp.route("/xero/create_customer", methods=["POST"])
def create_customer_route():
    """Create a fake customer in Xero only if they don't already exist."""

    # In real use you’d get this from request.json
    payload = {
        "Contacts": [
            {
                "Name": "Testy McTester",
                "FirstName": "Testy",
                "LastName": "McTester",
                "EmailAddress": "fake.customer@example.com",
                "Phones": [{"PhoneType": "MOBILE", "PhoneNumber": "123456789"}]
            }
        ]
    }

    result, error, status = create_contact(payload)
    if error:
        return jsonify(error), status
    return jsonify(result), status
