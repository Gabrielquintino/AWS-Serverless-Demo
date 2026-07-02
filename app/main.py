from fastapi import Depends, FastAPI, HTTPException, status

from app.lambda_handlers import CreateEventLambda, EventNotFoundError, GetEventStatusLambda
from app.models import EventAcceptedResponse, EventCreateRequest, EventStatusResponse

app = FastAPI(
    title="aws-serverless-demo",
    description="Local demo of an async serverless event processing flow.",
    version="1.0.0",
)


def get_create_event_lambda() -> CreateEventLambda:
    return CreateEventLambda()


def get_get_event_lambda() -> GetEventStatusLambda:
    return GetEventStatusLambda()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/events",
    response_model=EventAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_event(
    request: EventCreateRequest,
    handler: CreateEventLambda = Depends(get_create_event_lambda),
) -> EventAcceptedResponse:
    return handler.handle(request)


@app.get("/events/{event_id}", response_model=EventStatusResponse)
def get_event(
    event_id: str,
    handler: GetEventStatusLambda = Depends(get_get_event_lambda),
) -> EventStatusResponse:
    try:
        return handler.handle(event_id)
    except EventNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
