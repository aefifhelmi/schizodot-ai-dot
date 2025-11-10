import boto3
from datetime import datetime
from app.core.config import settings
from botocore.exceptions import ClientError

def dynamo_resource():
    return boto3.resource("dynamodb", region_name=settings.AWS_REGION)

def put_log(item: dict):
    dynamo = dynamo_resource()
    table = dynamo.Table(settings.DYNAMO_TABLE)
    if "timestamp" not in item:
        item["timestamp"] = datetime.utcnow().isoformat()
    try:
        table.put_item(Item=item)
    except ClientError as e:
        raise
    return item
