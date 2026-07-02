import json

import pytest

from worker.main import EventWorker


class FakeRepository:
    def __init__(self) -> None:
        self.updates: list[dict] = []

    def update_event_status(self, event_id: str, status: str, result=None, error=None):
        self.updates.append(
            {
                "event_id": event_id,
                "status": status,
                "result": result,
                "error": error,
            }
        )


class FakeSQSClient:
    def __init__(self) -> None:
        self.deleted: list[dict] = []

    def delete_message(self, QueueUrl: str, ReceiptHandle: str):
        self.deleted.append(
            {
                "queue_url": QueueUrl,
                "receipt_handle": ReceiptHandle,
            }
        )


def test_worker_processes_message_and_deletes_it():
    repository = FakeRepository()
    sqs_client = FakeSQSClient()
    worker = EventWorker(
        repository=repository,
        sqs_client=sqs_client,
        queue_url="http://localstack:4566/000000000000/events-queue",
    )
    message = {
        "Body": json.dumps(
            {
                "event_id": "evt-123",
                "event_type": "order.created",
                "payload": {"order_id": "123", "amount": 199.9},
            }
        ),
        "ReceiptHandle": "abc-123",
    }

    worker.process_sqs_message(message)

    assert repository.updates[0]["status"] == "PROCESSING"
    assert repository.updates[1]["status"] == "PROCESSED"
    assert repository.updates[1]["result"]["payload_keys"] == ["amount", "order_id"]
    assert sqs_client.deleted == [
        {
            "queue_url": "http://localstack:4566/000000000000/events-queue",
            "receipt_handle": "abc-123",
        }
    ]


def test_worker_marks_failed_message_without_deleting_it():
    repository = FakeRepository()
    sqs_client = FakeSQSClient()
    worker = EventWorker(
        repository=repository,
        sqs_client=sqs_client,
        queue_url="http://localstack:4566/000000000000/events-queue",
    )

    def broken_result(_body):
        raise RuntimeError("Unexpected processing error")

    worker.build_result = broken_result

    message = {
        "Body": json.dumps(
            {
                "event_id": "evt-456",
                "event_type": "order.created",
                "payload": {"order_id": "456"},
            }
        ),
        "ReceiptHandle": "receipt-456",
    }

    with pytest.raises(RuntimeError):
        worker.process_sqs_message(message)

    assert repository.updates[0]["status"] == "PROCESSING"
    assert repository.updates[1]["status"] == "FAILED"
    assert repository.updates[1]["error"] == "Unexpected processing error"
    assert sqs_client.deleted == []
