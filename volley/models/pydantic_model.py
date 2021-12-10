from typing import Any, Dict, NamedTuple, Optional, Type, TypeVar

from pydantic import BaseModel, Extra

from volley.models.base import BaseModelHandler

BaseModelType = TypeVar("BaseModelType", bound=BaseModel)


class PydanticModelHandler(BaseModelHandler):
    """for pydantic model that offloads serialization to serializer"""

    def construct(self, message: dict[str, Any], schema: Type[BaseModelType]) -> BaseModelType:
        """coverts a dict to a Pydantic model"""
        return schema.parse_obj(message)

    def deconstruct(self, model: BaseModelType) -> Dict[str, Any]:
        """converts a pydantic model to a dict"""
        return model.dict()


class PydanticParserModelHandler(BaseModelHandler):
    """pydantic model that handles serialization internally"""

    def construct(self, message: bytes, schema: Type[BaseModelType]) -> BaseModelType:
        """coverts bytes to a Pydantic model"""
        return schema.parse_raw(message)

    def deconstruct(self, model: BaseModelType) -> bytes:
        """converts a pydantic model to bytes"""
        return model.json().encode("utf-8")


class ComponentMessage(BaseModel):
    """default class for all workers"""

    class Config:
        extra = Extra.allow


class QueueMessage(BaseModel):
    """message in its raw state off a queue
    message_id: any identifier for a message on a queue.
        used for deleting or markng a message as success after post-processing
    """

    message_id: Any
    message: Any


class ConnectorTransport(NamedTuple):
    """transport object between connector and  engine

    message_context: any object. used to pass data or configuration between
        consumption actions; consume, delete, on_fail, shutdown.
        for example - database connection, Kafka message context, etc.
    message: raw message from connector
    timeout: when a connector returns none -
    """

    message_context: Optional[Any]
    message: Optional[Any]
