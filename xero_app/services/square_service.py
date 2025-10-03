from square import Square
from config import SQUARE_ACCESS_TOKEN, SQUARE_ENV

client = Square(token=SQUARE_ACCESS_TOKEN, environment=SQUARE_ENV)

def extract_services_from_order(order):
    """
    Extract services, variation names, prices, and quantities
    for Beauty Services and Photoshoot Deposit Collections.
    """
    services, variation_names, prices, quantities = [], [], [], []

    if not getattr(order, "line_items", None):
        return services, variation_names, prices, quantities

    ALLOWED_NAMES = {
        "beauty services (discounted)",
        "deposit - photoshoot collections",
    }

    for li in order.line_items:
        name = (getattr(li, "name", "") or "").lower()
        if name not in ALLOWED_NAMES:
            continue

        services.append(li.name)
        variation_names.append(getattr(li, "variation_name", None))
        prices.append(
            (getattr(li, "total_money", None).amount if getattr(li, "total_money", None) else 0) / 100
        )
        quantities.append(int(getattr(li, "quantity", "0")))

    return services, variation_names, prices, quantities


def get_order(order_id):
    order_resp = client.orders.get(order_id)
    order = order_resp.order
    return order
    # return client.orders.retrieve_order(order_id).body.get("order")


def get_customer(customer_id):
    return client.customers.get(customer_id).customer

def format_tender_reference(order) -> str:
    """
    Return a human-readable reference string for the tender (payment method).
    """
    if not order.tenders or len(order.tenders) == 0:
        return "Square"

    tender = order.tenders[0]

    if tender.type == "CARD" and tender.card_details and tender.card_details.card:
        brand = getattr(tender.card_details.card, "card_brand", "CARD")
        last4 = getattr(tender.card_details.card, "last_4", "")
        return f"Square {brand} ****{last4}"

    elif tender.type == "CASH":
        return "Square Cash"

    elif tender.type == "OTHER":
        return "EXTERNAL"

    else:
        return f"Square {tender.type}"
