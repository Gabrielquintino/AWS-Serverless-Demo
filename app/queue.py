import json
from typing import Any

from app.aws_clients import get_boto3_client
from app.settings import get_settings


class EventQueuePublisher:
    def __init__(self, sqs_client=None, queue_url: str | None = None) -> None:
        settings = get_settings()
        self.sqs_client = sqs_client or get_boto3_client("sqs")
        self.queue_url = queue_url or settings.sqs_queue_url

    def publish(self, message: dict[str, Any]) -> None:
        self.sqs_client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(message),
        )
