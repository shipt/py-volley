import logging
import os
from typing import List, Tuple

from pydantic import BaseModel

from volley import Engine
from volley.connectors.zmq import ZMQConsumer, ZMQProducer
from volley.logging import logger
from volley.models import PydanticModelHandler
from volley.serializers import MsgPackSerialization

logging.basicConfig(level=logging.INFO)

ZMQ_PORT = os.getenv("ZMQ_PORT", 5555)


class InputMessage(BaseModel):
    height: float
    weight: float
    req_id: int = 0


class BMI(BaseModel):
    bmi: float


cfg = {
    "request": {
        "value": "zmq",
        "consumer": ZMQConsumer,
        "serializer": MsgPackSerialization,
        "model_handler": PydanticModelHandler,
        "data_model": InputMessage,
        "config": {"port": ZMQ_PORT},
    },
    "response": {
        "value": "zmq",
        "producer": ZMQProducer,
        "serializer": MsgPackSerialization,
        "model_handler": PydanticModelHandler,
        "data_model": BMI,
        "config": {"port": ZMQ_PORT},
    },
}


eng = Engine(input_queue="request", output_queues=["response"], queue_config=cfg)


def calc_bmi(height: float, weight: float) -> BMI:
    return BMI(bmi=(weight / (height ** 2)))


@eng.stream_app
async def main(msg: InputMessage) -> List[Tuple[str, BMI]]:
    logger.info(msg)
    bmi = calc_bmi(height=msg.height, weight=msg.weight)
    return [("response", bmi)]


if __name__ == "__main__":
    main()
