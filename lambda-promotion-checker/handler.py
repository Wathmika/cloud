import boto3
import json
import urllib.request
from datetime import datetime, timedelta

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
ses = boto3.client("ses", region_name="ap-south-1")
table = dynamodb.Table("Promotions")

SENDER_EMAIL = "wathmikasilva@gmail.com"
ADMIN_EMAIL = "wathmikasilva@gmail.com"
PRODUCT_API_BASE = "https://4kjvzmcuh6.execute-api.ap-south-1.amazonaws.com/prod"

def get_product_name(product_id):
    try:
        url = f"{PRODUCT_API_BASE}/api/v1/products/{product_id}"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("name", product_id)
    except Exception as e:
        print(f"[WARNING] Could not fetch product name: {e}")
        return product_id

def handler(event, context):
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=5)

    response = table.scan()
    promotions = response.get("Items", [])

    newly_started = []
    for promo in promotions:
        start_time_str = promo.get("start_time")
        if not start_time_str:
            continue
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            continue

        if start_time.tzinfo is not None:
            start_time = start_time.replace(tzinfo=None)

        if window_start <= start_time <= now:
            newly_started.append(promo)

    for promo in newly_started:
        product_id = promo.get("product_id")
        discount = promo.get("discount_percentage")
        product_name = get_product_name(product_id)

        print(f"[PROMOTION] New promotion started: {product_name}, {discount}% off")

        try:
            ses.send_email(
                Source=SENDER_EMAIL,
                Destination={"ToAddresses": [ADMIN_EMAIL]},
                Message={
                    "Subject": {"Data": f"Flash Sale Started — {discount}% off {product_name}"},
                    "Body": {
                        "Text": {
                            "Data": f"A new promotion just started!\n\nProduct: {product_name}\nDiscount: {discount}%\n\n— SmartRetailX"
                        }
                    },
                },
            )
        except Exception as e:
            print(f"[WARNING] SES send failed: {e}")

    return {"statusCode": 200, "promotions_found": len(newly_started)}