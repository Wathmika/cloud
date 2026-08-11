import boto3
import redis

from app.config import settings

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=settings.dynamodb_endpoint,
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)

redis_client = redis.Redis(
    host=settings.redis_host, port=settings.redis_port, decode_responses=True
)

def create_table():
    existing = [t.name for t in dynamodb.tables.all()]
    if settings.products_table_name not in existing:
        dynamodb.create_table(
            TableName=settings.products_table_name,
            KeySchema=[{"AttributeName": "product_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "product_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

def get_products_table():
    return dynamodb.Table(settings.products_table_name)