from typing import Any, Dict

from pydantic import BaseModel


class BundleMessage(BaseModel):
    # TODO: needs to be standardized across a kafka message and rsmq
    # rsmq has its own schema and kafka has headers, etc.
    message_id: str
    params: Dict[str, Any]
    message: Dict[str, Any]
