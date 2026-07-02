import pytest

from app.lambda_handlers import CreateEventLambda
from app.models import EventCreateRequest


class FakeRepository:
    def __init__(self) -> None:
        self.created: list[dict] = []
        self.updated: list[dict] = []

    def create_event(self, event_id: str, event_type: str, payload: dict):
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
            "status": "RECEIVED",
            "created_at": "2026-07-02T10:00:00Z",
            "updated_at": "2026-07-02T10:00:00Z",
        }
        self.created.append(event)
        return event

    def update_event_status(self, event_id: str, status: str, result=None, error=None):
        self.updated.append(
            {
                "event_id": event_id,
                "status": status,
                "result": result,
                "error": error,
            }
        )


class FakeQueuePublisher:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.messages: list[dict] = []

    def publish(self, message: dict) -> None:
        if self.should_fail:
            raise RuntimeError("SQS is unavailable")
        self.messages.append(message)


def test_create_event_lambda_persists_and_enqueues():
    repository = FakeRepository()
    queue = FakeQueuePublisher()
    handler = CreateEventLambda(repository=repository, queue_publisher=queue)

    response = handler.handle(
        EventCreateRequest(
            event_type="order.created",
            payload={"order_id": "123"},
        )
    )

    assert response.status == "RECEIVED"
    assert len(repository.created) == 1
    assert len(queue.messages) == 1
    assert queue.messages[0]["event_type"] == "order.created"


def test_create_event_lambda_marks_event_as_failed_when_queue_breaks():
    repository = FakeRepository()
    queue = FakeQueuePublisher(should_fail=True)
    handler = CreateEventLambda(repository=repository, queue_publisher=queue)

    with pytest.raises(RuntimeError):
        handler.handle(
            EventCreateRequest(
                event_type="order.created",
                payload={"order_id": "123"},
            )
        )

    assert len(repository.updated) == 1
    assert repository.updated[0]["status"] == "FAILED"
    assert "Could not enqueue message" in repository.updated[0]["error"]
