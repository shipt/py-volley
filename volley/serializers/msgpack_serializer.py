from typing import Any, Dict

import msgpack

from volley.serializers.base import BaseSerialization


class MsgPackSerialization(BaseSerialization):
    def serialize(self, message: Dict[Any, Any]) -> bytes:
        serialized: bytes = msgpack.packb(message)
        return serialized

    def deserialize(self, message: bytes) -> Dict[str, Any]:
        deserialized: Dict[str, Any] = msgpack.unpackb(message)
        return deserialized
