# 🗂️ Understanding Square’s Order & Catalog Structure

### 🔹 Fetching Orders
```python
orders_resp = client.orders.search(
    location_ids=[os.getenv("SQUARE_PROD_LOCATION_ID")],
    limit=20
)
```
- Returns the **20 most recent orders** (by default, sorted by `created_at DESC`).  
- You must supply a `location_id` to scope the search.  

---

### 🔹 What You Get in Each Line Item
An `order.line_item` only contains a subset of fields:
- **`name`** → the label shown at checkout/invoices.  
  - Can be overridden when the order is created (so it’s not guaranteed to match the catalog exactly).  
- **`catalog_object_id`** → the ID of the *variation* that was sold.  
- ❌ **No `product_type` field here.**

---

### 🔹 Where `product_type` Lives
- `product_type` (e.g. `"APPOINTMENTS_SERVICE"`) exists **only at the `ITEM` level** in the catalog.  
- Variations (`ITEM_VARIATION`) do not carry this information.  

👉 To check if a line item is an appointment service:  
1. Fetch the variation via `catalog_object_id`.  
2. Climb up to its parent `ITEM`.  
3. Read `parent_obj.item_data.product_type`.  

Square explicitly designed **`product_type`** as the authoritative flag for classification.  
This is safer than matching names (since names can be edited or duplicated).  

---

### 🔹 Example Product Types
Here are some real mappings between `product_type` and line items:

```
Product Type: LEGACY_SQUARE_ONLINE_SERVICE | Line Item: Sitting Fee
Product Type: DIGITAL                     | Line Item: * Digital Images
Product Type: APPOINTMENTS_SERVICE        | Line Item: Beauty Services (Discounted)
Product Type: APPOINTMENTS_SERVICE        | Line Item: Deposit - Photoshoot Collections
Product Type: APPOINTMENTS_SERVICE        | Line Item: Photo Session *
Product Type: APPOINTMENTS_SERVICE        | Line Item: Viewing session - 80 min
Product Type: APPOINTMENTS_SERVICE        | Line Item: Viewing Session *
```

---

✅ **Summary:**  
- Orders → line items → give you *what was sold*, but not its `product_type`.  
- Catalog → items → hold the authoritative `product_type`.  
- To reliably detect appointments, always resolve from `line_item.catalog_object_id` → `ITEM_VARIATION`.

always have non zero for adding to liability/asset accounts

CREATE square sandbox orders API:
- square generates an order and assignts it an ID
- square automatically POSTs a webhook event to the ngrok webhook URL
- my app recieves it, looks up with order and processes it
- CHANGE THE ID !!!!!!!!!!!!
curl -X POST https://connect.squareupsandbox.com/v2/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer EAAAl5efZNkbZekL9iFt3xweRklurTd_qewnDtVzhAVYNwCyzc9DHT85Nm2KpTUq" \
  -d "{
    \"idempotency_key\": \"order-photo-key-00003\",
    \"order\": {
      \"location_id\": \"L8WZ7MFH47TB3\",
      \"customer_id\": \"R3CVD1XWDFV910YCXE2H19ZJ24\",
      \"line_items\": [
        {
          \"quantity\": \"1\",
          \"catalog_object_id\": \"TVUEDLXUVIDW72IBOPFS7OAL\"
        },
        {
          \"quantity\": \"1\",
          \"catalog_object_id\": \"SG4CVFAOSMFG3GKFNH62XRTL\"
        }
      ]
    }
  }"

create item variation:

curl -X POST https://connect.squareupsandbox.com/v2/catalog/object \
  -H "Authorization: Bearer EAAAl5efZNkbZekL9iFt3xweRklurTd_qewnDtVzhAVYNwCyzc9DHT85Nm2KpTUq" \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "create-appointments-service-001",
    "object": {
      "type": "ITEM",
      "id": "#TEMP_APPT_ITEM",
      "item_data": {
        "name": "Beauty Services",
        "product_type": "APPOINTMENTS_SERVICE",
        "variations": [
          {
            "type": "ITEM_VARIATION",
            "id": "#TEMP_APPT_VARIATION",
            "item_variation_data": {
              "name": "Makeup Session",
              "pricing_type": "FIXED_PRICING",
              "price_money": {
                "amount": 0,
                "currency": "USD"
              }
            }
          }
        ]
      }
    }
  }'

  curl -X POST https://connect.squareupsandbox.com/v2/catalog/object \
  -H "Authorization: Bearer EAAAl5efZNkbZekL9iFt3xweRklurTd_qewnDtVzhAVYNwCyzc9DHT85Nm2KpTUq" \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "create-appointments-service-002",
    "object": {
      "type": "ITEM",
      "id": "#TEMP_APPT_ITEM2",
      "item_data": {
        "name": "Photoshoot Collections",
        "product_type": "APPOINTMENTS_SERVICE",
        "variations": [
          {
            "type": "ITEM_VARIATION",
            "id": "#TEMP_APPT_VARIATION2",
            "item_variation_data": {
              "name": "Collection: Self-Love [High Key]",
              "pricing_type": "FIXED_PRICING",
              "price_money": {
                "amount": 5000,
                "currency": "USD"
              }
            }
          }
        ]
      }
    }
  }'

  create square account (R3CVD1XWDFV910YCXE2H19ZJ24)
  curl -X POST https://connect.squareupsandbox.com/v2/customers \
  -H "Authorization: Bearer EAAAl5efZNkbZekL9iFt3xweRklurTd_qewnDtVzhAVYNwCyzc9DHT85Nm2KpTUq" \
  -H "Content-Type: application/json" \
  -d '{
    "given_name": "Testy",
    "family_name": "McTester",
    "email_address": "fake.customer@example.com",
    "phone_number": "+12045109160"
  }' 

fake payment: 

curl -X POST "https://connect.squareupsandbox.com/v2/payments" \
  -H "Authorization: Bearer EAAAl5efZNkbZekL9iFt3xweRklurTd_qewnDtVzhAVYNwCyzc9DHT85Nm2KpTUq" \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "idempotency-12345-'"$(date +%s)"'",
    "amount_money": {
      "amount": 5000,
      "currency": "USD"
    },
    "autocomplete": false,
    "order_id": "MGRpfBV7VDRyE6A3s2OsB6iHJc4F",
    "location_id": "L8WZ7MFH47TB3",
      "source_id": "EXTERNAL",
    "external_details": {
      "type": "OTHER",
      "source": "External Provider (Sandbox simulation)"
    },
    "note": "Recorded external payment for testing"
  }'

curl -X POST "https://connect.squareupsandbox.com/v2/orders" \
  -H "Authorization: Bearer EAAAl5efZNkbZekL9iFt3xweRklurTd_qewnDtVzhAVYNwCyzc9DHT85Nm2KpTUq" \
  -H "Content-Type: application/json" \
  -d '{
    "order": {
      "location_id": "L8WZ7MFH47TB3",
      "customer_id": "R3CVD1XWDFV910YCXE2H19ZJ24",
      "line_items": [
        {
          "name": "Beauty Services (Discounted)",
          "quantity": "1",
          "base_price_money": {
            "amount": 7500,
            "currency": "USD"
          },
          "variation_name": "Makeup and Hair Styling Session"
        },
        {
          "name": "Deposit - Photoshoot Collections",
          "quantity": "1",
          "base_price_money": {
            "amount": 10000,
            "currency": "USD"
          },
          "variation_name": "Collection: Self-Love [High Key]"
        }
      ]
    },
    "idempotency_key": "test-$(uuidgen)"
  }'

