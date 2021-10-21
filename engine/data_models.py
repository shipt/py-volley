from typing import Any, Dict, Union

from pydantic import BaseModel, Field


class ComponentMessage(BaseModel):
    """base class for all inputs/outputs from a componet"""


class QueueMessage(BaseModel):
    # standardized across a kafka message and rsmq
    # rsmq has its own schema and kafka has headers, etc.
    message_id: Any = Field(description="identifier for the message in the queue. e.g. kafka Offset")
    message: Union[Dict[str, Any], ComponentMessage]
