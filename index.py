from square import Square
import os
from dotenv import load_dotenv

load_dotenv()

client = Square(token=os.getenv("SQUARE_ACCESS_TOKEN"))

orders_resp = client.orders.search(
    location_ids=[os.getenv("SQUARE_LOCATION_ID")],
    limit=10
)

orders = orders_resp.orders or []

for order in orders:
    services, prices, quantities = [], [], []

    if order.line_items:
        for li in order.line_items:
            catalog_id = li.catalog_object_id
            if not catalog_id:
                continue
            if order.customer_id:
                cust_resp = client.customers.get(order.customer_id)
                cust = cust_resp.customer
                print("Customer display name:", f"{cust.given_name} {cust.family_name}")

            catalog_resp = client.catalog.object.get(catalog_id)
            catalog_obj = catalog_resp.object

            parent_obj = None
            if catalog_obj.type == "ITEM_VARIATION":
                parent_item_id = catalog_obj.item_variation_data.item_id
                parent_resp = client.catalog.object.get(parent_item_id)
                parent_obj = parent_resp.object
            elif catalog_obj.type == "ITEM":
                parent_obj = catalog_obj

            if parent_obj and parent_obj.item_data:
                product_type = parent_obj.item_data.product_type

                if product_type == "APPOINTMENTS_SERVICE":
                    services.append(li.name)
                    prices.append(li.total_money.amount if li.total_money else 0)
                    quantities.append(int(li.quantity))

    if services:  # only print if we found appointment services
        print("Order:", order.id)
        print("  Services:", services)
        print("  Prices:", prices)
        print("  Quantities:", quantities)
