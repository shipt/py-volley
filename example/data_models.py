from typing import List, Optional

from volley.data_models import GenericMessage


class InputMessage(GenericMessage):
    request_id: str
    list_of_values: List[float]
    msg_counter: int = 0

    class Config:
        schema_extra = {
            "examples": [
                {
                    "request_id": "request-id-1234",
                    "list_of_values": [1, 2, 3, 4.5],
                }
            ]
        }


class Queue1Message(GenericMessage):
    request_id: str
    max_value: float
    msg_counter: int = 0

    class Config:
        schema_extra = {
            "examples": [
                {
                    "request_id": "request-id-1234",
                    "max_value": 4.5,
                }
            ]
        }


class OutputMessage(GenericMessage):
    request_id: str
    max_plus: float
    msg_counter: int = 0

    class Config:
        schema_extra = {
            "examples": [
                {
                    "request_id": "request-id-1234",
                    "max_plus": 5.5,
                }
            ]
        }


class PostgresMessage(GenericMessage):
    request_id: str
    max_plus: float
    msg_counter: Optional[int] = 0

    class Config:
        schema_extra = {
            "examples": [
                {
                    "request_id": "request-id-1234",
                    "max_plus": 5.5,
                }
            ]
        }


class KafkaKafkaInput(GenericMessage):
    request_id: str


class KafkaKafkaOutput(GenericMessage):
    request_id: str
    counter: int


class RedisOutput(GenericMessage):
    request_id: str
    counter: int
