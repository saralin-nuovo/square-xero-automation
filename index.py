# from square import Square
# import os
# from dotenv import load_dotenv

# load_dotenv()

# client = Square(token=os.getenv("SQUARE_PROD_ACCESS_TOKEN"))

# orders_resp = client.orders.search(
#     location_ids=[os.getenv("SQUARE_PROD_LOCATION_ID")],
#     limit=10
# )

# orders = orders_resp.orders or []

# for order in orders:
#     services, prices, quantities = [], [], []

#     if order.line_items:
#         for li in order.line_items:
#             catalog_id = li.catalog_object_id
#             if not catalog_id:
#                 continue
#             if order.customer_id:
#                 cust_resp = client.customers.get(order.customer_id)
#                 cust = cust_resp.customer
#                 print("Customer display name:", f"{cust.given_name} {cust.family_name}")

#             catalog_resp = client.catalog.object.get(catalog_id)
#             catalog_obj = catalog_resp.object

#             parent_obj = None
#             if catalog_obj.type == "ITEM_VARIATION":
#                 parent_item_id = catalog_obj.item_variation_data.item_id
#                 parent_resp = client.catalog.object.get(parent_item_id)
#                 parent_obj = parent_resp.object
#             elif catalog_obj.type == "ITEM":
#                 parent_obj = catalog_obj

#             if parent_obj and parent_obj.item_data:
#                 product_type = parent_obj.item_data.product_type

#                 if product_type == "APPOINTMENTS_SERVICE":
#                     services.append(li.name)
#                     prices.append(li.total_money.amount if li.total_money else 0)
#                     quantities.append(int(li.quantity))

#     if services:  # only print if we found appointment services
#         print("Order:", order.id)
#         print("  Services:", services)
#         print("  Prices:", prices)
#         print("  Quantities:", quantities)
from flask import Flask, redirect, request
import os
from dotenv import load_dotenv
from xero_python.api_client import ApiClient, Configuration
from xero_python.api_client.oauth2 import OAuth2Session, OAuth2Token

load_dotenv()

CLIENT_ID = os.getenv("XERO_CLIENT_ID")
CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("XERO_REDIRECT_URI")

app = Flask(__name__)

# OAuth2 session
oauth2_session = OAuth2Session(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=["accounting.transactions", "offline_access"]
)

@app.route("/xero/connect")
def connect_xero():
    # Generate the login URL
    auth_url, state = oauth2_session.create_authorization_url()
    print("👉 Auth URL:", auth_url)
    return redirect(auth_url)

@app.route("/xero/callback")
def callback_xero():
    code = request.args.get("code")
    print("✅ Callback hit. Code:", code)

    try:
        # Exchange code for tokens
        token = oauth2_session.fetch_token(code=code)
        print("Access token:", token["access_token"])
        print("Refresh token:", token["refresh_token"])
        return "Xero tokens retrieved, check console logs."
    except Exception as e:
        print("❌ Token error:", e)
        return {"token_error": str(e)}, 400

if __name__ == "__main__":
    app.run(port=5001, debug=True)



# ⚡ Step 3: After login, Xero redirects to your redirect_uri with a `code` param.
# Exchange that code for tokens:
# token = api_client.get_access_token(code)

# ⚡ Step 4: Save the token (you’ll use this in future calls)
# api_client.set_oauth2_token(OAuth2Token(token))

# Example: call Accounting API once authenticated
# accounting_api = AccountingApi(api_client)
# invoices = accounting_api.get_invoices(xero_tenant_id)
# print("Invoices:", invoices)



# {
#   "id": "VADlh2ria85Z6NH2SbmB5BmB9fZZY",
#   "location_id": "L71XXT7NHQ2D3",
#   "reference_id": null,
#   "source": {
#     "name": "Invoices"
#   },
#   "customer_id": "J008FJQT7VFGA087YCB2YKHHGM",
#   "line_items": [
#     {
#       "uid": "ea7746a6-6804-4a72-9bc4-23014331ed53",
#       "name": "Payments 2/2",
#       "quantity": "1",
#       "quantity_unit": null,
#       "note": null,
#       "catalog_object_id": null,
#       "catalog_version": null,
#       "variation_name": null,
#       "item_type": "ITEM",
#       "metadata": null,
#       "modifiers": null,
#       "applied_taxes": null,
#       "applied_discounts": null,
#       "applied_service_charges": null,
#       "base_price_money": {
#         "amount": 391444,
#         "currency": "USD"
#       },
#       "variation_total_price_money": {
#         "amount": 391444,
#         "currency": "USD"
#       },
#       "gross_sales_money": {
#         "amount": 391444,
#         "currency": "USD"
#       },
#       "total_tax_money": {
#         "amount": 0,
#         "currency": "USD"
#       },
#       "total_discount_money": {
#         "amount": 0,
#         "currency": "USD"
#       },
#       "total_money": {
#         "amount": 391444,
#         "currency": "USD"
#       },
#       "pricing_blocklists": {
#         "blocked_discounts": null,
#         "blocked_taxes": [
#           {
#             "uid": "8464187f7f4b4485d8fcf584f5d06a2a",
#             "tax_uid": null,
#             "tax_catalog_object_id": "VUEBM4CI2MYXATZKIMPDVV4H"
#           }
#         ]
#       },
#       "total_service_charge_money": {
#         "amount": 0,
#         "currency": "USD"
#       }
#     }
#   ],
#   "taxes": null,
#   "discounts": null,
#   "service_charges": null,
#   "fulfillments": [
#     {
#       "uid": "hEZQCGiwYk5VANWQCjep2C",
#       "type": "SHIPMENT",
#       "state": "PROPOSED",
#       "line_item_application": null,
#       "entries": null,
#       "metadata": null,
#       "pickup_details": null,
#       "shipment_details": {
#         "recipient": {
#           "customer_id": null,
#           "display_name": "Ismarys Mato Cabrera",
#           "email_address": "ismarysmato@icloud.com",
#           "phone_number": null,
#           "address": null
#         },
#         "carrier": null,
#         "shipping_note": null,
#         "shipping_type": null,
#         "tracking_number": null,
#         "tracking_url": null,
#         "placed_at": null,
#         "in_progress_at": null,
#         "packaged_at": null,
#         "expected_shipped_at": null,
#         "shipped_at": null,
#         "canceled_at": null,
#         "cancel_reason": null,
#         "failed_at": null,
#         "failure_reason": null
#       },
#       "delivery_details": null
#     }
#   ],
#   "returns": null,
#   "return_amounts": null,
#   "net_amounts": {
#     "total_money": {
#       "amount": 391444,
#       "currency": "USD"
#     },
#     "tax_money": {
#       "amount": 0,
#       "currency": "USD"
#     },
#     "discount_money": {
#       "amount": 0,
#       "currency": "USD"
#     },
#     "tip_money": {
#       "amount": 0,
#       "currency": "USD"
#     },
#     "service_charge_money": {
#       "amount": 0,
#       "currency": "USD"
#     }
#   },
#   "rounding_adjustment": null,
#   "tenders": null,
#   "refunds": null,
#   "metadata": null,
#   "created_at": "2025-09-30T14:03:29.464Z",
#   "updated_at": "2025-09-30T14:03:30.157Z",
#   "closed_at": null,
#   "state": "OPEN",
#   "version": 4,
#   "total_money": {
#     "amount": 391444,
#     "currency": "USD"
#   },
#   "total_tax_money": {
#     "amount": 0,
#     "currency": "USD"
#   },
#   "total_discount_money": {
#     "amount": 0,
#     "currency": "USD"
#   },
#   "total_tip_money": {
#     "amount": 0,
#     "currency": "USD"
#   },
#   "total_service_charge_money": {
#     "amount": 0,
#     "currency": "USD"
#   },
#   "ticket_name": null,
#   "pricing_options": null,
#   "rewards": null,
#   "net_amount_due_money": {
#     "amount": 391444,
#     "currency": "USD"
#   }
# }
