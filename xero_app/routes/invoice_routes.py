# routes/invoice_routes.py
from flask import Blueprint, jsonify, request
from services.xero_service import fetch_invoices, create_invoice

invoice_bp = Blueprint("invoice", __name__)

@invoice_bp.route("/xero/invoices")
def get_invoices():
    data, error, status = fetch_invoices(page=1)
    if error:
        return jsonify(error), status
    return jsonify(data), status


@invoice_bp.route("/xero/create_invoice", methods=["POST"])
def create_invoice_route():
    # Either accept body from request.json, or use a default
    invoice_body = request.json or {
        "Invoices": [
            {
                "Type": "ACCREC",
                "Contact": {"Name": "Test Customer"},
                "LineItems": [
                    {
                        "Description": "Deposit payment",
                        "Quantity": 1,
                        "UnitAmount": 11.00,
                        "AccountCode": "260",
                        "TaxType": "TAX001"
                    }
                ],
                "Date": "2025-10-01",
                "DueDate": "2025-10-15",
                "InvoiceNumber": "DEP-348586",
                "Status": "AUTHORISED"
            }
        ]
    }

    data, error, status = create_invoice(invoice_body)
    if error:
        return jsonify(error), status
    return jsonify(data), status
