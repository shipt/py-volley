from typing import Any

import msgpack

from volley.serializers.base import BaseSerialization


class MsgPackSerialization(BaseSerialization):
    def serialize(self, message: dict[Any, Any]) -> bytes:
        serialized: bytes = msgpack.packb(message)
        return serialized

    def deserialize(self, message: bytes) -> dict[str, Any]:
        deserialized: dict[str, Any] = msgpack.unpackb(message)
        return deserialized
