from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from engine.data_models import ComponentMessage


class InputMessage(ComponentMessage):
    """input messages coming off kafka"""

    bundle_request_id: str

    # list of order id
    orders: List[str]

    class Config:
        schema_extra = {
            "examples": [
                {
                    "bundle_request_id": "request-id-1234",
                    "orders": ["invalid-order_1", "invalid-order_2", "16578146", "16643507", "16731513"],
                }
            ]
        }


class TriageMessage(ComponentMessage):
    """message read in by the Triage component

    Currently output by Features component
    """

    enriched_orders: List[Dict[str, Any]]
    bundle_request_id: str
    engine_event_id: str
    error_orders: Optional[List[Dict[str, Any]]] = None

    class Config:
        schema_extra = {
            "examples": [
                {
                    "bundle_request_id": "request-id-1234",
                    "engine_request_id": "uuid4-engine-internal",
                    "enriched_orders": [
                        {
                            "order_id": "16578146",
                            "item_qty": 3,
                            "shop_time_minutes": 20,
                            "delivery_start_time": "2021-08-26 17:00:00Z",
                            "delivery_end_time": "2021-08-26 18:00:00Z",
                            "store_name": "Target",
                            "delv_longitude": -73.919696,
                            "delv_latitude": 40.827675,
                            "store_longitude": -73.930287,
                            "store_latitude": 40.823963,
                        }
                    ],
                    "error_orders": ["bad_order_1", "bad_order_1"],
                }
            ]
        }


class OptimizerMessage(ComponentMessage):
    """Message expected by Optimizer component"""

    bundle_request_id: str
    engine_event_id: str
    grouped_orders: List[List[Dict[str, Any]]]
    error_orders: Optional[List[Dict[str, Any]]] = None

    class Config:
        schema_extra = {
            "examples": [
                {
                    "bundle_request_id": "request-id-123",
                    "engine_event_id": "engine-id-123",
                    "grouped_orders": [
                        [
                            {
                                "order_id": "16578146",
                                "item_qty": 3,
                                "shop_time_minutes": 20,
                                "delivery_start_time": "2021-08-26 17:00:00Z",
                                "delivery_end_time": "2021-08-26 18:00:00Z",
                                "store_name": "Target",
                                "delv_longitude": -73.919696,
                                "delv_latitude": 40.827675,
                                "store_longitude": -73.930287,
                                "store_latitude": 40.823963,
                            }
                        ]
                    ],
                    "error_orders": [
                        {"order_id": "bad_order_1"},
                        {"order_id": "bad_order_1"},
                    ],
                }
            ]
        }


# COLLECTOR
class CollectorMessage(ComponentMessage):
    """base message schema for all messages published to the collector"""

    # TODO: should explore sharing pydantic model w/ SqlAlchemy
    engine_event_id: str
    bundle_request_id: str


class CollectTriage(CollectorMessage):
    """contains attributes for triage events
    triage events are created by traige component and indicate the start of optimizer and fallback processing
    """

    event_type: str = "triage"
    timeout: str


class Bundle(BaseModel):
    """defines an individual bundle"""

    group_id: str
    orders: List[str]

    class Config:
        schema_extra = {
            "examples": [
                {
                    "group_id": "group_a",
                    "orders": ["15855965", "158559635", "15812355965"],
                }
            ]
        }


class CollectOptimizer(CollectorMessage):
    """contains attributes for finished optimizers
    optimizer publishes its results to the collector in this format
    """

    event_type: str = "optimizer"
    optimizer_id: str
    optimizer_results: Dict[str, List[Bundle]]
    optimizer_finish: str


class CollectFallback(CollectorMessage):
    """contains attributres for finished fallback solutions
    fallback component publishes its results to the collector in this format
    """

    event_type: str = "fallback"
    fallback_id: str
    fallback_results: Dict[str, List[Bundle]]
    fallback_finish: str


class PublisherInput(ComponentMessage):
    engine_event_id: str
    bundle_request_id: str
    optimizer_id: Optional[str]
    optimizer_results: Optional[Dict[str, Any]]
    optimizer_finish: Optional[str]
    fallback_id: Optional[str]
    fallback_results: Optional[Dict[str, Any]]
    fallback_finish: Optional[str]


class PublisherMessage(ComponentMessage):
    """schema for the message on the publisher queue (postgres) and read by the publisher component"""

    # TODO: should explore sharing pydantic model w/ SqlAlchemy
    # triage inserts
    results: List[CollectorMessage]


class OutputMessage(ComponentMessage):
    """schema for messages leaving the bundle-engine and going to kafka for backend engineering"""

    engine_event_id: str
    bundle_request_id: str

    # data model for output
    bundles: List[Bundle]

    class Config:
        schema_extra = {
            "examples": [
                {
                    "bundle_request_id": "request-id-1234",
                    "engine_request_id": "uuid4-engine-internal",
                    "bundles": [Bundle.schema()["examples"][0]],
                }
            ]
        }


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
    store_location_id: int = Field(example=2110)
    store_latitude: float = Field(example=42.99678)
    store_longitude: float = Field(example=-85.59336)


class EnrichedOrder(Order):
    """base order definition plus features added from flight plan"""

    shop_time_minutes: int = Field(example=20)


def get_example(model: BaseModel) -> Dict[str, Any]:
    """helper function for generating sample data from a base class model"""
    return {k: v["example"] for k, v in model.schema()["properties"].items()}
