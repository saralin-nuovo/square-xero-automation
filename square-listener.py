from flask import Flask, request, jsonify
from square import Square
from square.environment import SquareEnvironment
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("SQUARE_SANDBOX_ACCESS_TOKEN")

client = Square(token=ACCESS_TOKEN, environment=SquareEnvironment.SANDBOX)

app = Flask(__name__)

# ------------------ Helper Function ------------------

def extract_services_from_order(order):
    """Extract services, prices (after discounts), and quantities for appointment services."""
    services, prices, quantities = [], [], []

    if not order.line_items:
        return services, prices, quantities

    for li in order.line_items:
        catalog_id = li.catalog_object_id
        if not catalog_id:
            continue

        # Fetch catalog object
        catalog_resp = client.catalog.object.get(catalog_id)
        catalog_obj = catalog_resp.object

        if catalog_obj.type == "ITEM_VARIATION":
            parent_item_id = catalog_obj.item_variation_data.item_id
            parent_resp = client.catalog.object.get(parent_item_id)
            parent_obj = parent_resp.object

            if parent_obj and parent_obj.item_data.product_type == "APPOINTMENTS_SERVICE":
                services.append(li.name)
                prices.append(li.total_money.amount / 100 if li.total_money else 0)
                quantities.append(int(li.quantity))

    return services, prices, quantities

# ------------------ Webhook Route ------------------

@app.route("/square-webhook", methods=["POST"])
def square_webhook():
    event = request.get_json()
    print("📩 New Square event:", event)

    if event.get("type") == "order.created":
        order_id = event["data"]["object"]["order_created"]["order_id"]
        print("✅ New order created:", order_id)

        # Fetch full order details
        order_resp = client.orders.get(order_id)
        order = order_resp.order

        # Fetch customer info
        if order.customer_id:
            cust_resp = client.customers.get(order.customer_id)
            cust = cust_resp.customer
            print("Customer:", f"{cust.given_name} {cust.family_name}")

        # Use helper to extract service info
        services, prices, quantities = extract_services_from_order(order)

        if services:
            print("🗒️ Order:", order.id)
            print("  Services:", services)
            print("  Prices:", prices)
            print("  Quantities:", quantities)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
