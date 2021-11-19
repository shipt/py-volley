from typing import Any, Dict, TypeVar, Union

from pydantic import BaseModel, Extra, Field


class ComponentMessage(BaseModel):
    """base class for all inputs/outputs from a componet"""

    class Config:
        extra = Extra.allow


class QueueMessage(BaseModel):
    # standardized across a kafka message and rsmq
    # rsmq has its own schema and kafka has headers, etc.
    message_id: Any = Field(description="identifier for the message in the queue")
    message: Union[Dict[str, Any], ComponentMessage]


ComponentMessageType = TypeVar("ComponentMessageType", bound=ComponentMessage)
