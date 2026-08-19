import json
import boto3

ses = boto3.client("ses", region_name="ap-south-1")
SENDER_EMAIL = "wathmikasilva@gmail.com"

def handler(event, context):
    for record in event.get("Records", []):
        message = json.loads(record["Sns"]["Message"])
        order_id = message.get("order_id")
        customer_email = message.get("customer_email")

        print(f"[NOTIFICATION] Order {order_id} confirmed — email sent to {customer_email}")

        try:
            ses.send_email(
                Source=SENDER_EMAIL,
                Destination={"ToAddresses": [customer_email]},
                Message={
                    "Subject": {"Data": f"SmartRetailX — Order #{order_id} Confirmed"},
                    "Body": {
                        "Text": {
                            "Data": (
                                f"Hi there,\n\n"
                                f"Thanks for your order! Here's a quick summary:\n\n"
                                f"Order ID: {order_id}\n"
                                f"Status: Confirmed\n\n"
                                f"We'll notify you again once your order ships.\n\n"
                                f"— The SmartRetailX Team"
                            )
                        }
                    },
                },
            )
        except Exception as e:
            print(f"[WARNING] SES send failed: {e}")

    return {"statusCode": 200}