import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    aws_endpoint_url: str
    aws_region: str
    aws_access_key_id: str
    aws_secret_access_key: str
    dynamodb_table_name: str
    sqs_queue_name: str
    sqs_queue_url: str


@lru_cache
def get_settings() -> Settings:
    aws_endpoint_url = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566").rstrip("/")
    sqs_queue_name = os.getenv("SQS_QUEUE_NAME", "events-queue")
    return Settings(
        aws_endpoint_url=aws_endpoint_url,
        aws_region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        dynamodb_table_name=os.getenv("DYNAMODB_TABLE_NAME", "events-table"),
        sqs_queue_name=sqs_queue_name,
        sqs_queue_url=os.getenv(
            "SQS_QUEUE_URL",
            f"{aws_endpoint_url}/000000000000/{sqs_queue_name}",
        ),
    )
