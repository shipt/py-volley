from typing import Any, Dict

import orjson

from volley.serializers.base import BaseSerialization


class OrJsonSerialization(BaseSerialization):
    def serialize(self, message: Dict[Any, Any]) -> bytes:
        serialized: bytes = orjson.dumps(message, option=orjson.OPT_NAIVE_UTC, default=str)
        return serialized

    def deserialize(self, message: bytes) -> Dict[str, Any]:
        deserialized: Dict[str, Any] = orjson.loads(message)
        return deserialized
