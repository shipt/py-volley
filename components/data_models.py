from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytz
from pydantic import BaseModel, Extra, Field

from engine.data_models import ComponentMessage


def get_example(model: BaseModel) -> Dict[str, Any]:
    """helper function for generating sample data from a base class model"""
    return {k: v["example"] for k, v in model.schema()["properties"].items()}


class Order(BaseModel):
    """defines an individual order"""

    # TODO: which of these can be optional?
    order_id: str = Field(example="15855965")
    order_type: str = Field(example="marketplace")  # TODO: should be enum maybe?
    delivery_start_time: datetime = Field(example="2020-12-28T08:00:00+00:00")
    delivery_end_time: datetime = Field(example="2020-12-28T09:00:00+00:00")
    schedule_id: int = Field(example=86337511)
    schedule_type: str = Field(example="deliver_between")
    delivery_by: datetime = Field(example="2020-01-01T00:00:00+00:00")
    delivery_latitude: float = Field(example=42.967167)
    delivery_longitude: float = Field(example=-85.53964)
    total_items: int = Field(example="0")
    metro_id: str = Field(example="")

    store_location_id: int = Field(example=2110)

    class Config:
        """the examples service as a smoke-test
        given a batch of these 4 orders:
            order_ids 16702212 and 16578146 should always bundle together
            15830545 and 15855965 should never bundle together
        """

        __now = datetime.utcnow().replace(tzinfo=pytz.UTC)

        extra = Extra.allow
        schema_extra = {
            "examples": [
                {
                    "order_id": "16702212",
                    "order_type": "marketplace",
                    "delivery_start_time": __now.isoformat("T"),
                    "delivery_end_time": (__now + timedelta(hours=1)).isoformat("T"),
                    "schedule_id": "86337511",
                    "schedule_type": "deliver_between",
                    "delivery_by": "2021-11-04T19:11:12.920811+00:00",
                    "delivery_latitude": 42.985558,
                    "delivery_longitude": -85.58836,
                    "total_items": "16",
                    "metro_id": "61",
                    "store_id": "10",
                    "store_location_id": "2110",
                },
                {
                    "order_id": "16578146",
                    "order_type": "platform",
                    "delivery_start_time": __now.isoformat("T"),
                    "delivery_end_time": (__now + timedelta(hours=1)).isoformat("T"),
                    "schedule_id": "86989913",
                    "schedule_type": "deliver_between",
                    "delivery_by": "2021-11-04T19:11:12.920811+00:00",
                    "delivery_latitude": 42.99678,
                    "delivery_longitude": -85.59336,
                    "total_items": "6",
                    "metro_id": "61",
                    "store_id": "10",
                    "store_location_id": "2110",
                },
                {
                    "order_id": "15830545",
                    "order_type": "marketplace",
                    "delivery_start_time": __now.isoformat("T"),
                    "delivery_end_time": (__now + timedelta(hours=1)).isoformat("T"),
                    "schedule_id": "70253593",
                    "schedule_type": "deliver_between",
                    "delivery_by": "2021-11-04T19:11:12.920811+00:00",
                    "delivery_latitude": 44.977753,
                    "delivery_longitude": -93.265015,
                    "total_items": "0",
                    "metro_id": "",
                    "store_id": "",
                    "store_location_id": "2110",
                },
                {
                    "order_id": "15855965",
                    "order_type": "marketplace",
                    "delivery_start_time": __now.isoformat("T"),
                    "delivery_end_time": (__now + timedelta(hours=1)).isoformat("T"),
                    "schedule_id": "70253593",
                    "schedule_type": "deliver_between",
                    "delivery_by": "2021-11-04T19:11:12.920811+00:00",
                    "delivery_latitude": 31.554689,
                    "delivery_longitude": -110.281998,
                    "total_items": "0",
                    "metro_id": "",
                    "store_id": "",
                    "store_location_id": "2110",
                },
            ]
        }


class EnrichedOrder(Order):
    """base order definition plus features added from flight plan + metro service"""

    shop_time_minutes: float = Field(example=17.25)
    store_latitude: float = Field(example=42.99678)
    store_longitude: float = Field(example=-85.59336)

    class Config:
        schema_extra = {
            "examples": [
                {
                    "order_id": "16702212",
                    "order_type": "marketplace",
                    "delivery_start_time": "2021-11-04T18:11:12.920811+00:00",
                    "delivery_end_time": "2021-11-04T19:11:12.920811+00:00",
                    "schedule_id": "86337511",
                    "schedule_type": "deliver_between",
                    "delivery_by": "2021-11-04T19:11:12.920811+00:00",
                    "delivery_latitude": 42.985558,
                    "delivery_longitude": -85.58836,
                    "total_items": "16",
                    "metro_id": "61",
                    "store_id": "10",
                    "store_location_id": "2110",
                    "shop_time_minutes": 17.25,
                    "store_latitude": 42.9967809,
                    "store_longitude": -85.59336449999999,
                }
            ]
        }


class InputMessage(ComponentMessage):
    """input messages coming off kafka"""

    bundle_request_id: str

    # list of order id
    orders: List[Order]

    class Config:
        schema_extra = {
            "examples": [
                {
                    "bundle_request_id": "request-id-1234",
                    "orders": Order.schema()["examples"],
                }
            ]
        }


class TriageMessage(ComponentMessage):
    """message read in by the Triage component

    Currently output by Features component
    """

    bundle_request_id: str
    engine_event_id: str
    enriched_orders: List[EnrichedOrder]
    error_orders: Optional[List[Order]] = None

    class Config:
        schema_extra = {
            "examples": [
                {
                    "bundle_request_id": "request-id-1234",
                    "engine_request_id": "uuid4-engine-internal",
                    "enriched_orders": [EnrichedOrder.schema()["examples"][0]],
                    "error_orders": [Order.schema()["examples"][0]],
                }
            ]
        }


class OptimizerMessage(ComponentMessage):
    """Message expected by Optimizer component"""

    bundle_request_id: str
    engine_event_id: str
    grouped_orders: List[List[EnrichedOrder]]
    error_orders: Optional[List[Order]] = None

    class Config:
        schema_extra = {
            "examples": [
                {
                    "bundle_request_id": "request-id-123",
                    "engine_event_id": "engine-id-123",
                    "grouped_orders": [[EnrichedOrder.schema()["examples"][0]]],
                    "error_orders": [Order.schema()["examples"][0]],
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

    class Config:
        __now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        schema_extra = {
            "examples": [
                {
                    "results": [
                        {
                            "engine_event_id": "2ceedf0d-7bbf-45d3-9a04-75354dafefa6",
                            "bundle_request_id": "request-id-0",
                            "timeout": __now + timedelta(minutes=5),
                            "optimizer_finish": __now,
                            "optimizer_results": {
                                "bundles": [
                                    {
                                        "group_id": "ec5f0532-6093-4e83-ad56-0085bf7347a0",
                                        "orders": ["16578146", "16702212"],
                                    },
                                    {"group_id": "ed1f1db6-9d11-4dd2-ab58-a5c997f3e4c6", "orders": ["15830545"]},
                                    {"group_id": "6fa8a39e-f168-4e64-ad3b-53f9d225a180", "orders": ["15855965"]},
                                ]
                            },
                            "fallback_id": "afa60f17-36d8-4a3b-b68c-b3e0513b0492",
                            "fallback_results": {
                                "bundles": [
                                    {"group_id": "g1234", "orders": ["order_1", "order2", "order_4"]},
                                    {"group_id": "g1235", "orders": ["order_3"]},
                                ]
                            },
                            "fallback_finish": __now,
                            "optimizer_id": "d97d7a2d-e492-41ac-a6ce-5dc8a3e6a01d",
                        }
                    ]
                }
            ]
        }


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
