from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BundleMessage(BaseModel):
    # standardized across a kafka message and rsmq
    # rsmq has its own schema and kafka has headers, etc.
    message_id: Any = Field(
        description="identifier for the message in the queue. e.g. kafka Offset"
    )
    params: Dict[str, Any]
    message: Dict[str, Any]


class CollectorMessage(BaseModel):
    # TODO: should explore sharing pydantic model w/ SqlAlchemy
    # triage inserts
    engine_event_id: str
    bundle_event_id: Optional[str]
    store_id: Optional[str]
    timeout: Optional[str]  # only used in Triage

    # fallback updates
    fallback_id: Optional[str] = None
    fallback_results: Optional[Dict[str, Any]] = None
    fallback_finish: Optional[str] = None

    # optimizer updates
    optimizer_id: Optional[str]
    optimizer_results: Optional[Dict[str, Any]] = None
    optimizer_finish: Optional[str] = None

    def fallback_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "fallback",
            "engine_event_id": self.engine_event_id,
            "fallback_id": self.fallback_id,
            "fallback_results": self.fallback_results,
            "fallback_finish": self.fallback_finish,
        }

    def optimizer_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "optimizer",
            "engine_event_id": self.engine_event_id,
            "optimizer_id": self.optimizer_id,
            "optimizer_results": self.optimizer_results,
            "optimizer_finish": self.optimizer_finish,
        }

    def triage_dict(self) -> Dict[str, Any]:
        return {
            "engine_event_id": self.engine_event_id,
            "bundle_event_id": self.bundle_event_id,
            "store_id": self.store_id,
            "timeout": self.timeout,
        }


class OutputMessage(BaseModel):
    engine_event_id: str
    bundle_event_id: str
    store_id: str
    optimizer_type: str

    # TODO: List[Orders] or Dict[bundle_id: str, List[Orders]]
    # data model for output
    bundles: List[Any]
