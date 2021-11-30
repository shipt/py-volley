from typing import Any

from pydantic import BaseModel, Extra

from volley.validators.base import BaseValidation


class PydanticValidator(BaseValidation):
    def construct(self, message: dict[str, Any], schema: BaseModel) -> BaseModel:
        """coverts a dict to a Pydantic model"""
        return schema.parse_obj(message)


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
