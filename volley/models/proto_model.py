from typing import Any, Type, TypeVar

from google.protobuf.message import Message

from volley.models.base import BaseModelHandler

ProtoMessage = TypeVar("ProtoMessage", bound=Message)


class ProtoModelHandler(BaseModelHandler):
    def construct(self, message: bytes, schema: type) -> ProtoMessage:
        assert schema is not None
        obj: ProtoMessage = schema()
        obj.ParseFromString(message)
        return obj

    def deconstruct(self, model: ProtoMessage) -> Any:
        return model.SerializeToString()
