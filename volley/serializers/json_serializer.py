import json
from typing import Any, Dict

from volley.serializers.base import BaseSerialization


class JsonSerialization(BaseSerialization):
    def serialize(self, message: Dict[Any, Any]) -> bytes:
        serialized: bytes = json.dumps(message, default=str).encode("utf-8")
        return serialized

    def deserialize(self, message: bytes) -> Dict[str, Any]:
        deserialized: Dict[str, Any] = json.loads(message)
        return deserialized
