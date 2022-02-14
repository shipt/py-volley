from typing import Any, Dict, Type, TypeVar

from pydantic import BaseModel, Extra

from volley.models.base import BaseModelHandler

BaseModelType = TypeVar("BaseModelType", bound=BaseModel)


class PydanticModelHandler(BaseModelHandler):
    """for pydantic model that offloads serialization to serializer"""

    def construct(self, message: Dict[str, Any], schema: Type[BaseModelType]) -> BaseModelType:
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


class GenericMessage(BaseModel):
    """The default data model for all profiles.
    Serves as a flexible data model. Accepts extra attributes and provides no type validation.
    """

    class Config:
        extra = Extra.allow


class QueueMessage(BaseModel):
    """message in its raw state off a queue
    message_context: any identifier for a message on a queue.
        used for deleting or markng a message as success after post-processing
    """

    message_context: Any
    message: Any
