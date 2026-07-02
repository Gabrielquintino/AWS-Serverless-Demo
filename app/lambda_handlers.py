from uuid import uuid4

from app.models import EventAcceptedResponse, EventCreateRequest, EventStatusResponse
from app.queue import EventQueuePublisher
from app.repository import EventRepository


class EventNotFoundError(Exception):
    """Raised when an event does not exist in DynamoDB."""


class CreateEventLambda:
    def __init__(
        self,
        repository: EventRepository | None = None,
        queue_publisher: EventQueuePublisher | None = None,
    ) -> None:
        self.repository = repository or EventRepository()
        self.queue_publisher = queue_publisher or EventQueuePublisher()

    def handle(self, request: EventCreateRequest) -> EventAcceptedResponse:
        event_id = str(uuid4())
        event = self.repository.create_event(
            event_id=event_id,
            event_type=request.event_type,
            payload=request.payload,
        )

        message = {
            "event_id": event_id,
            "event_type": request.event_type,
            "payload": request.payload,
        }

        try:
            self.queue_publisher.publish(message)
        except Exception as exc:
            self.repository.update_event_status(
                event_id=event_id,
                status="FAILED",
                error=f"Could not enqueue message: {exc}",
            )
            raise

        return EventAcceptedResponse(
            event_id=event_id,
            status=event["status"],
            message="Event accepted for async processing.",
        )


class GetEventStatusLambda:
    def __init__(self, repository: EventRepository | None = None) -> None:
        self.repository = repository or EventRepository()

    def handle(self, event_id: str) -> EventStatusResponse:
        event = self.repository.get_event(event_id)
        if event is None:
            raise EventNotFoundError(f"Event '{event_id}' was not found.")

        return EventStatusResponse.model_validate(event)
