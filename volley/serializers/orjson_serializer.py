from typing import Any

import orjson

from volley.serializers.base import BaseSerialization


class OrJsonSerialization(BaseSerialization):
    def serialize(self, message: dict[Any, Any], *args: Any, **kwargs: Any) -> bytes:
        serialized: bytes = orjson.dumps(message, option=orjson.OPT_NAIVE_UTC, default=str)
        return serialized

    def deserialize(self, message: bytes, *args: Any, **kwargs: Any) -> dict[str, Any]:
        deserialized: dict[str, Any] = orjson.loads(message)
        return deserialized
