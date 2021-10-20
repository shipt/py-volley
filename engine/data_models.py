from typing import Any, Dict

from pydantic import BaseModel, Field


class QueueMessage(BaseModel):
    # standardized across a kafka message and rsmq
    # rsmq has its own schema and kafka has headers, etc.
    message_id: Any = Field(
        description="identifier for the message in the queue. e.g. kafka Offset"
    )
    message: Dict[str, Any]
