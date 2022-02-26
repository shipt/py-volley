import logging
from random import randint
from typing import Dict, List, Tuple, Union

from pydantic.main import BaseModel

from example.data_models import (
    InputMessage,
    OutputMessage,
    PostgresMessage,
    Queue1Message,
)
from example.plugins.my_plugin import MyPGConsumer
from volley.data_models import GenericMessage
from volley.engine import Engine
from volley.logging import logger
from volley.models.pydantic_model import PydanticModelHandler
from volley.serializers import MsgPackSerialization

logging.basicConfig(level=logging.INFO)

queue_config = {
    # define queue configurations in a dict
    # overrwrites any existing yaml configs
    "redis_queue": {
        "value": "long_name_1",
        "profile": "rsmq",
        "serializer": MsgPackSerialization,
        "data_model": GenericMessage,
        "model_handler": PydanticModelHandler,
    },
    "postgres_queue": {
        "value": "my_long_table_name",
        "data_model": "example.data_models.PostgresMessage",
        "model_handler": PydanticModelHandler,
        # disable serializer - sqlachemy implementation in example/plugin/my_plugin.py handles this
        "serializer": "disabled",
        # both dot path to the object or the object itself are valid
        "producer": "example.plugins.my_plugin.MyPGProducer",
        "consumer": MyPGConsumer,
    },
    "input-topic": {
        "value": "localhost.kafka.input",
        "profile": "confluent",
        "data_model": InputMessage,
    },
    "output-topic": {
        "value": "localhost.kafka.output",
        "profile": "confluent-pydantic",
        "data_model": OutputMessage,
    },
}

eng = Engine(
    input_queue="redis_queue",
    output_queues=["postgres_queue", "output-topic", "input-topic"],
    queue_config=queue_config,
)


@eng.stream_app
def main(msg: Queue1Message) -> Union[List[Tuple[str, BaseModel, Dict[str, str]]], List[Tuple[str, InputMessage]]]:
    """adds one to a value"""
    req_id = msg.request_id
    max_val = msg.max_value

    random_value = randint(0, 20)
    max_plus_jiggle = max_val + random_value
    # how many times have we seen this message?
    msg_count = msg.msg_counter
    logger.info(f"{msg_count=}")

    if random_value > 10:
        recycled_msg = InputMessage(request_id=req_id, list_of_values=[max_plus_jiggle], msg_counter=msg_count + 1)
        logger.info(f"Recycling - {recycled_msg.dict()}")
        return [("input-topic", recycled_msg)]

    # we didn't meet the random recycle threshold, so continue forward
    output_msg = OutputMessage(request_id=req_id, max_plus=max_plus_jiggle)
    pg_msg = PostgresMessage(request_id=req_id, max_plus=max_plus_jiggle)

    logger.info(output_msg.dict())
    logger.info(pg_msg.dict())
    return [("postgres_queue", pg_msg), ("output-topic", output_msg, {"key": "partitionKeyOne"})]  # type: ignore


if __name__ == "__main__":
    main()
