from typing import Any

from app.aws_clients import get_boto3_resource
from app.settings import get_settings
from app.utils import normalize_value, utc_now_iso


class EventRepository:
    def __init__(self, dynamodb_resource=None, table_name: str | None = None) -> None:
        settings = get_settings()
        resource = dynamodb_resource or get_boto3_resource("dynamodb")
        self.table = resource.Table(table_name or settings.dynamodb_table_name)

    def create_event(
        self,
        event_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        timestamp = utc_now_iso()
        item = {
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
            "status": "RECEIVED",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self.table.put_item(Item=item)
        return item

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        response = self.table.get_item(Key={"event_id": event_id})
        item = response.get("Item")
        if item is None:
            return None
        return normalize_value(item)

    def update_event_status(
        self,
        event_id: str,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        attributes: dict[str, Any] = {
            "status": status,
            "updated_at": utc_now_iso(),
        }
        if result is not None:
            attributes["result"] = result
        if error is not None:
            attributes["error"] = error

        update_expression = "SET " + ", ".join(
            f"#{field_name} = :{field_name}" for field_name in attributes
        )
        expression_attribute_names = {
            f"#{field_name}": field_name for field_name in attributes
        }
        expression_attribute_values = {
            f":{field_name}": field_value for field_name, field_value in attributes.items()
        }

        response = self.table.update_item(
            Key={"event_id": event_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )
        return normalize_value(response.get("Attributes", {}))
