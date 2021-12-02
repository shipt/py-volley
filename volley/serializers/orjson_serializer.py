from typing import Any

import orjson

from ..serializers.base import BaseSerialization


class OrJsonSerialization(BaseSerialization):
    def serialize(self, message: dict[Any, Any]) -> bytes:
        serialized: bytes = orjson.dumps(message, option=orjson.OPT_NAIVE_UTC, default=str)
        return serialized

    def deserialize(self, message: bytes) -> dict[str, Any]:
        deserialized: dict[str, Any] = orjson.loads(message)
        return deserialized
