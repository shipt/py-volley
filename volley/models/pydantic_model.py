from typing import Any, Dict, List, Type, TypeVar

from pydantic import BaseModel, ConfigDict, TypeAdapter

from volley.models.base import BaseModelHandler

BaseModelType = TypeVar("BaseModelType", bound=BaseModel)


class PydanticModelHandler(BaseModelHandler):
    """for pydantic model that offloads serialization to serializer"""

    def construct(self, message: Dict[str, Any], schema: Type[BaseModelType]) -> BaseModelType:
        """coverts a dict to a Pydantic model"""
        return schema.model_validate(message)

    def deconstruct(self, model: BaseModelType) -> Dict[str, Any]:
        """converts a pydantic model to a dict"""
        return model.model_dump()


class PydanticParserModelHandler(BaseModelHandler):
    """pydantic model that handles serialization internally"""

    def construct(self, message: bytes, schema: Type[BaseModelType]) -> BaseModelType:
        """coverts bytes to a Pydantic model"""
        return schema.model_validate_json(message)

    def deconstruct(self, model: BaseModelType) -> bytes:
        """converts a pydantic model to bytes"""
        return model.model_dump_json().encode("utf-8")


class PydanticListParser(BaseModelHandler):
    """for pydantic model that offloads serialization to serializer"""

    def construct(self, message: List[Any], schema: Type[BaseModelType]) -> List[BaseModelType]:
        """coverts a dict to a Pydantic model"""
        Adapter = TypeAdapter(type=List[schema])  # type: ignore
        return Adapter.validate_python(message)

    def deconstruct(self, model: List[BaseModelType]) -> List[Dict[str, Any]]:
        """converts a pydantic model to a dict"""
        return [m.model_dump() for m in model]


class GenericMessage(BaseModel):
    """The default data model for all profiles.
    Serves as a flexible data model. Accepts extra attributes and provides no type validation.
    """

    model_config = ConfigDict(extra="allow")


class QueueMessage(BaseModel):
    """message in its raw state off a queue
    message_context: any identifier for a message on a queue.
        used for deleting or markng a message as success after post-processing
    """

    message_context: Any = None
    message: Any = None
