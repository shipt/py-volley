from typing import Any, Dict, NamedTuple, TypeVar, Union

from pydantic import BaseModel, Extra


class ComponentMessage(BaseModel):
    """base class for all inputs/outputs from a componet"""

    class Config:
        extra = Extra.allow


class QueueMessage(BaseModel):
    """message in its raw state off a queue
    message_id: any identifier for a message on a queue.
        used for deleting or markng a message as success after post-processing
    """

    message_id: Any
    message: Union[Dict[str, Any], ComponentMessage]


ComponentMessageType = TypeVar("ComponentMessageType", bound=ComponentMessage)
