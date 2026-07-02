import json
import logging
import time
from typing import Any

from botocore.exceptions import ClientError

from app.aws_clients import get_boto3_client
from app.repository import EventRepository
from app.settings import get_settings
from app.utils import utc_now_iso

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
LOGGER = logging.getLogger(__name__)


class EventWorker:
    def __init__(
        self,
        repository: EventRepository | None = None,
        sqs_client=None,
        queue_url: str | None = None,
        poll_interval: int = 2,
    ) -> None:
        settings = get_settings()
        self.repository = repository or EventRepository()
        self.sqs_client = sqs_client or get_boto3_client("sqs")
        self.queue_url = queue_url or settings.sqs_queue_url
        self.poll_interval = poll_interval

    def run_forever(self) -> None:
        LOGGER.info("Worker started and listening to %s", self.queue_url)
        while True:
            self.poll_once()
            time.sleep(self.poll_interval)

    def poll_once(self) -> None:
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=10,
                VisibilityTimeout=30,
            )
        except ClientError as exc:
            LOGGER.warning("Could not poll SQS yet: %s", exc)
            return

        for message in response.get("Messages", []):
            self.process_sqs_message(message)

    def process_sqs_message(self, message: dict[str, Any]) -> None:
        payload = json.loads(message["Body"])
        self.process_event(payload)
        self.sqs_client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )

    def process_event(self, payload: dict[str, Any]) -> None:
        event_id = payload["event_id"]
        LOGGER.info("Processing event %s", event_id)
        self.repository.update_event_status(event_id=event_id, status="PROCESSING")

        try:
            result = self.build_result(payload)
            self.repository.update_event_status(
                event_id=event_id,
                status="PROCESSED",
                result=result,
            )
        except Exception as exc:
            self.repository.update_event_status(
                event_id=event_id,
                status="FAILED",
                error=str(exc),
            )
            LOGGER.exception("Event %s failed", event_id)
            raise

    def build_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        message_payload = payload.get("payload", {})
        return {
            "summary": f"Event {payload['event_id']} processed successfully",
            "processed_at": utc_now_iso(),
            "event_type": payload.get("event_type"),
            "payload_keys": sorted(message_payload.keys()),
        }


if __name__ == "__main__":
    EventWorker().run_forever()
