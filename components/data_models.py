from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InputMessage:
    """input messages coming off kafka"""

    orders: str


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


class BaseMessage(BaseModel):
    """base for messages that component functions read in. each message has at least"""

    engine_event_id: str
    bundle_event_id: Optional[str]


class PublisherMessage(BaseMessage):
    """schema for the message on the publisher queue (postgres) and read by the publisher component"""

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


class Bundle(BaseModel):
    """defines an individual bundle"""

    group_id: str
    orders: List[int]


class Order(BaseModel):
    """defines an individual order"""

    # TODO: which of these can be optional?
    order_id: str = Field(example="15855965")
    order_type: str = Field(example="marketplace")  # TODO: should be enum maybe?
    delivery_start_time: datetime = Field(example="2020-12-28T08:00:00Z")
    delivery_end_time: datetime = Field(example="2020-12-28T09:00:00Z")
    schedule_id: int = Field(example=86337511)
    schedule_type: str = Field(example="deliver_between")
    delivery_by: datetime = Field(example="2020-01-01T00:00:00Z")
    delivery_latitude: float = Field(example=42.967167)
    delivery_longitude: float = Field(example=-85.53964)
    total_items: int = Field(example="0")
    metro_id: str = Field(example="")
    store_id: str = Field(example="")
    store_location_id: int = Field(example=2110)
    store_latitude: float = Field(example=42.99678)
    store_longitude: float = Field(example=-85.59336)


class EnrichedOrder(Order):
    """base order definition plus features added from flight plan"""

    shop_time_minutes: int = Field(example=20)


def get_example(model: BaseModel) -> Dict[str, Any]:
    """helper function for generating sample data from a base class model"""
    return {k: v["example"] for k, v in model.schema()["properties"].items()}
