import pytest
from httpx import ASGITransport, AsyncClient

from app.lambda_handlers import EventNotFoundError
from app.main import app, get_create_event_lambda, get_get_event_lambda


class FakeCreateEventLambda:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def handle(self, request):
        self.requests.append(request.model_dump())
        return {
            "event_id": "evt-123",
            "status": "RECEIVED",
            "message": "Event accepted for async processing.",
        }


class FakeGetEventStatusLambda:
    def __init__(self, response=None) -> None:
        self.response = response

    def handle(self, event_id: str):
        if self.response is None:
            raise EventNotFoundError(f"Event '{event_id}' was not found.")
        return self.response


@pytest.mark.anyio
async def test_create_event_returns_202():
    fake_handler = FakeCreateEventLambda()
    app.dependency_overrides[get_create_event_lambda] = lambda: fake_handler

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/events",
                json={
                    "event_type": "order.created",
                    "payload": {"order_id": "123"},
                },
            )

        assert response.status_code == 202
        assert response.json()["event_id"] == "evt-123"
        assert fake_handler.requests == [
            {"event_type": "order.created", "payload": {"order_id": "123"}}
        ]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_event_returns_persisted_status():
    fake_handler = FakeGetEventStatusLambda(
        response={
            "event_id": "evt-123",
            "event_type": "order.created",
            "payload": {"order_id": "123"},
            "status": "PROCESSED",
            "created_at": "2026-07-02T10:00:00Z",
            "updated_at": "2026-07-02T10:00:03Z",
            "result": {
                "summary": "Event evt-123 processed successfully",
                "processed_at": "2026-07-02T10:00:03Z",
                "event_type": "order.created",
                "payload_keys": ["order_id"],
            },
            "error": None,
        }
    )
    app.dependency_overrides[get_get_event_lambda] = lambda: fake_handler

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/events/evt-123")

        assert response.status_code == 200
        assert response.json()["status"] == "PROCESSED"
        assert response.json()["result"]["payload_keys"] == ["order_id"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_event_returns_404_when_missing():
    fake_handler = FakeGetEventStatusLambda()
    app.dependency_overrides[get_get_event_lambda] = lambda: fake_handler

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/events/missing-id")

        assert response.status_code == 404
        assert "missing-id" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
