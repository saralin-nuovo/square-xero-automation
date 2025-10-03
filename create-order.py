from square import Square
import os
from dotenv import load_dotenv

load_dotenv()

client = Square(token=os.getenv("SQUARE_PROD_ACCESS_TOKEN"))

orders_resp = client.orders.search(
    location_ids=[os.getenv("SQUARE_PROD_LOCATION_ID")],
    limit=20
)

orders = orders_resp.orders or []

for order in orders:
    if order.line_items:
        for li in order.line_items:
            catalog_id = li.catalog_object_id
            if not catalog_id:
                continue

            # Fetch the variation object directly
            catalog_resp = client.catalog.object.get(catalog_id)
            catalog_obj = catalog_resp.object

            if catalog_obj.type == "ITEM_VARIATION":
                variation_name = catalog_obj.item_variation_data.name
                parent_item_id = catalog_obj.item_variation_data.item_id
                parent_resp = client.catalog.object.get(parent_item_id)
                parent_obj = parent_resp.object
                product_type = parent_obj.item_data.product_type
                if product_type == "APPOINTMENTS_SERVICE":
                    price = (li.total_money.amount if li.total_money else 0)/100
                    print(order)
                    # print(
                    #     "Product Type:", product_type,
                    #     "| Line Item:", li.name,
                    #     "| Price:", f"${price:.2f}" if price is not None else "N/A"
                    # )