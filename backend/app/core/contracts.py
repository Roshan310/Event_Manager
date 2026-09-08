"""Deterministic synthetic examples shared by OpenAPI and the frontend reference."""

from typing import Any

UUID = "11111111-1111-4111-8111-111111111111"


def example(schema: dict[str, Any], schemas: dict[str, Any], key: str = "") -> Any:
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        if name == "CheckInRequest":
            return {"registration_id": UUID}
        if name == "EventUpdate":
            return {"title": "Updated community meetup"}
        if name == "EventOut":
            result = example(schemas[name], schemas, key)
            result["status"] = "published"
            result["confirmed_count"], result["available_seats"] = 1, 99
            return result
        return example(schemas[name], schemas, key)
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    if "anyOf" in schema:
        if any(s.get("type") == "null" for s in schema["anyOf"]):
            return None
        return example(next(s for s in schema["anyOf"] if s.get("type") != "null"), schemas, key)
    if "default" in schema:
        return schema["default"]
    kind = schema.get("type")
    if kind == "object":
        return {
            name: example(value, schemas, name)
            for name, value in schema.get("properties", {}).items()
        }
    if kind == "array":
        return [example(schema["items"], schemas)]
    if kind == "boolean":
        return key != "has_more"
    if kind in ("integer", "number"):
        return {
            "capacity": 100,
            "available_seats": 99,
            "limit": 20,
            "offset": 0,
            "expires_in": 900,
            "revision": 1,
            "attempts": 1,
        }.get(key, 1)
    if schema.get("format") == "uuid":
        return UUID
    if schema.get("format") == "date-time":
        return "2027-01-15T06:15:00Z" if key != "ends_at" else "2027-01-15T08:15:00Z"
    if schema.get("format") == "email":
        return "person@example.com"
    values = {
        "name": "Community member",
        "title": "Community meetup",
        "description": "Meet local people and share ideas.",
        "location": "Kathmandu",
        "timezone": "Asia/Kathmandu",
        "status": "published",
        "message": "Operation completed",
        "code": "state_conflict",
        "request_id": "example-request-id",
        "topic": "registration.confirmed",
        "action": "event.published",
        "qr_payload": UUID + "." + "a" * 64,
        "qr_url": f"http://localhost:8000/api/v1/events/{UUID}/registrations/me/ticket/qr",
    }
    if "password" in key:
        return "example-password-change-me"
    if "token" in key:
        return "synthetic-example-token-not-a-real-credential-123456789"
    return values.get(key, "example")


def add_examples(document: dict[str, Any]) -> dict[str, Any]:
    schemas = document.get("components", {}).get("schemas", {})
    for operations in document["paths"].values():
        for operation in operations.values():
            for media in operation.get("requestBody", {}).get("content", {}).values():
                if "schema" in media:
                    media["example"] = example(media["schema"], schemas)
            for code, response in operation.get("responses", {}).items():
                media = response.get("content", {}).get("application/json")
                if media and "schema" in media:
                    if int(code) >= 400:
                        media["example"] = {
                            "error": {
                                "code": {
                                    "400": "invalid_action_token",
                                    "401": "session_revoked",
                                    "403": "forbidden",
                                    "404": "event_not_found",
                                    "409": "registration_closed",
                                    "413": "image_too_large",
                                    "422": "validation_error",
                                    "429": "rate_limited",
                                    "500": "internal_error",
                                    "503": "not_ready",
                                }.get(code, "http_error"),
                                "message": response["description"],
                                "details": {"retry_after": 60} if code == "429" else None,
                                "request_id": "example-request-id",
                            }
                        }
                    else:
                        media["example"] = example(media["schema"], schemas)
                        if operation.get("operationId", "").startswith("liveness_"):
                            media["example"] = {"status": "ok"}
                        elif operation.get("operationId", "").startswith("readiness_"):
                            media["example"] = {"status": "ready"}
    return document
