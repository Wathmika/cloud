import boto3

from app.config import settings

if settings.dynamodb_endpoint:
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=settings.dynamodb_endpoint,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
else:
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)

def create_table():
    existing = [t.name for t in dynamodb.tables.all()]
    if settings.inventory_table_name not in existing:
        dynamodb.create_table(
            TableName=settings.inventory_table_name,
            KeySchema=[{"AttributeName": "product_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "product_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

def get_inventory_table():
    return dynamodb.Table(settings.inventory_table_name)