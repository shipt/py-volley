import logging
from typing import Dict, List, Tuple

from pydantic import BaseModel

from example.data_models import InputMessage, Queue1Message
from volley import Engine
from volley.logging import logger

logging.basicConfig(level=logging.INFO)
from volley.connectors import ZMQConsumer, ZMQProducer
from volley.models import PydanticModelHandler
from volley.serializers import MsgPackSerialization


class InputMessage(BaseModel):
    hello: str


cfg = {
    "request": {
        "value": "zmq",
        "consumer": ZMQConsumer,
        "producer": ZMQProducer,
        "serializer": MsgPackSerialization,
        "model_handler": PydanticModelHandler,
        "data_model": InputMessage,
        "config": {"port": 5555},
    },
}


eng = Engine(input_queue="request", output_queues=["request"], queue_config=cfg)


@eng.stream_app
async def main(msg: InputMessage) -> List[Tuple[str, Queue1Message, Dict[str, float]]]:
    logger.info(msg)
    msg.hello = "dog" + msg.hello
    return [("request", msg)]


if __name__ == "__main__":
    main()
