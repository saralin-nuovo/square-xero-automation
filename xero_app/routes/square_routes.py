from flask import Blueprint, request, jsonify
from services.square_service import format_tender_reference, get_order, get_customer, extract_services_from_order, client
from services.xero_service import find_or_create_contact_from_square, create_xero_invoice, get_xero_invoice_by_order_id, update_xero_invoice_reference

square_bp = Blueprint("square", __name__)

@square_bp.route("/square-webhook", methods=["POST"])
def square_webhook():
    event = request.get_json()
    print("📩 New Square event:", event)

    if event.get("type") == "order.created":
        order_id = event["data"]["object"]["order_created"]["order_id"]
        print("✅ New order created:", order_id)

        order = get_order(order_id)

        services, variation_names, prices, quantities = extract_services_from_order(order)

        if services:
            if getattr(order, "customer_id", None):
                cust = get_customer(order.customer_id)
                if cust:
                    try:
                        xero_contact, created = find_or_create_contact_from_square(cust)
                        print(f"✅ Xero contact {'created' if created else 'found'}:")
                        items = []
                        for desc, var_name, price, qty in zip(services, variation_names, prices, quantities):
                            items.append({
                                "description": desc,  
                                "var_name": var_name,
                                "quantity": qty,
                                "unit_amount": price,
                            })
                        invoice = create_xero_invoice(
                            contact_id=xero_contact.get("ContactID"),
                            items=items,
                            square_order_id=order.id,
                            reference="Square (Pending Payment)"
                        )

                        print("🧾 Xero invoice created:", invoice)

                    except Exception as e:
                        print("❌ Xero contact/invoice sync error:", e)
    elif event.get("type") in ("payment.created", "payment.updated"):
        payment = event["data"]["object"]["payment"]
        order_id = payment.get("order_id")
        order = get_order(order_id)

        # Only update if we have the mapping
        invoice = get_xero_invoice_by_order_id(order_id)
        if invoice:
            invoice_id = invoice["InvoiceID"]
            ref_text = format_tender_reference(order)
            update_xero_invoice_reference(invoice_id, ref_text)

        if invoice_id:
            ref_text = format_tender_reference(order)

            update_xero_invoice_reference(
                invoice_id=invoice_id,
                reference=ref_text
            )
            print(f"🔄 Updated Xero invoice {invoice_id} with ref {ref_text}")

    return jsonify({"status": "ok"})


@square_bp.route("/square/latest-order", methods=["GET"])
def latest_order():
    """
    Fetch the most recent order and include customer info.
    """
    try:
        response = client.orders.search(
            limit=1,
            location_ids=["L71XXT7NHQ2D3"],  # replace with your sandbox location ID
            query={
                "sort": {
                    "sort_field": "CREATED_AT",
                    "sort_order": "DESC"
                }
            }
        )

        orders = response.orders
        if not orders:
            return jsonify({"message": "No orders found"}), 200

        order = orders[0]

        # Fetch customer info if present
        customer_info = None
        if getattr(order, "customer_id", None):
            cust_resp = client.customers.get(order.customer_id)
            cust = getattr(cust_resp, "customer", None)

            if cust:
                # Manually extract key fields
                customer_info = {
                    "id": getattr(cust, "id", None),
                    "given_name": getattr(cust, "given_name", None),
                    "family_name": getattr(cust, "family_name", None),
                    "email_address": getattr(cust, "email_address", None),
                    "phone_number": getattr(cust, "phone_number", None),
                    "created_at": getattr(cust, "created_at", None),
                    "updated_at": getattr(cust, "updated_at", None),
                }

        result = {
            "customer": customer_info
        }

        print("🆕 Most recent order:", result, flush=True)
        return "Check your console/logs for order + customer info"

    except Exception as e:
        print("❌ Error fetching latest order:", str(e), flush=True)
        return jsonify({"error": str(e)}), 500
