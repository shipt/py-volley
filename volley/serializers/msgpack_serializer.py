from typing import Any

import msgpack

from volley.serializers.base import BaseSerialization


class MsgPackSerialization(BaseSerialization):
    def serialize(self, message: dict[Any, Any], **kwargs) -> bytes:
        serialized: bytes = msgpack.packb(message)
        return serialized

    def deserialize(self, message: bytes, **kwargs) -> dict[str, Any]:
        deserialized: dict[str, Any] = msgpack.unpackb(message)
        return deserialized
