import orjson
from pydantic import BaseModel

from volley.serializers.base import BaseSerialization


class PydanticSerialization(BaseSerialization):
    def deserialize(self, message: bytes, model: BaseModel) -> BaseModel:
        deserialized: BaseModel = model.parse_raw(message)
        return deserialized

    def serialize(self, message: BaseModel) -> bytes:
        serialized = orjson.dumps(message, option=orjson.OPT_NAIVE_UTC, default=str)
        return serialized
