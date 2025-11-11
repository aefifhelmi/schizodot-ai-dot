# app/core/aws.py
import boto3
from botocore.config import Config
from core.config import settings

# Reuse one shared session
_session = boto3.session.Session(
    aws_access_key_id=None,              # let boto3 read from env/credentials
    aws_secret_access_key=None,          # keep None to use standard chain
    region_name=settings.AWS_REGION,
)

_boto_cfg = Config(
    retries={"max_attempts": 5, "mode": "standard"},
    connect_timeout=5,
    read_timeout=15,
    user_agent_extra="schizodot-fastapi/phase2",
)

def s3():
    return _session.client("s3", config=_boto_cfg)

def dynamodb():
    return _session.resource("dynamodb", config=_boto_cfg)
