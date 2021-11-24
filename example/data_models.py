from datetime import datetime
from typing import List

from volley.data_models import ComponentMessage


class InputMessage(ComponentMessage):
    request_id: str
    list_of_values: List[float]

    class Config:
        schema_extra = {
            "examples": [
                {
                    "request_id": "request-id-1234",
                    "list_of_values": [1, 2, 3, 4.5],
                }
            ]
        }


class Queue1Message(ComponentMessage):
    request_id: str
    max_value: float

    class Config:
        schema_extra = {
            "examples": [
                {
                    "request_id": "request-id-1234",
                    "max_value": 4.5,
                }
            ]
        }


class OutputMessage(ComponentMessage):
    request_id: str
    max_plus: float

    class Config:
        schema_extra = {
            "examples": [
                {
                    "request_id": "request-id-1234",
                    "max_plus": 5.5,
                }
            ]
        }

class PostgresMessage(ComponentMessage):
    request_id: str
    max_plus: float

    class Config:
        schema_extra = {
            "examples": [
                {
                    "request_id": "request-id-1234",
                    "max_plus": 5.5,
                }
            ]
        }
