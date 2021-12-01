import json
from typing import Any

from volley.serializers.base import BaseSerialization


class JsonSerialization(BaseSerialization):
    def serialize(self, message: dict[Any, Any]) -> bytes:
        serialized: bytes = json.dumps(message, default=str).encode("utf-8")
        return serialized

    def deserialize(self, message: bytes) -> dict[str, Any]:
        deserialized: dict[str, Any] = json.loads(message)
        return deserialized
