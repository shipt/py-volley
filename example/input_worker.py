import asyncio
import logging
from typing import Dict, List, Tuple

from confluent_kafka import Message

from example.data_models import InputMessage, Queue1Message
from volley import Engine
from volley.logging import logger

logging.basicConfig(level=logging.INFO)

eng = Engine(
    input_queue="input-topic",
    output_queues=["redis_queue"],
    yaml_config_path="./example/volley_config.yml",
    dead_letter_queue="dead-letter-queue",
)


async def fun1() -> None:
    logger.info("one")


async def fun2() -> None:
    logger.info("two")


@eng.stream_app
async def main(msg: InputMessage, msg_ctx: Message) -> List[Tuple[str, Queue1Message, Dict[str, float]]]:
    logger.info("Consumed partition: %s, offset: %s", msg_ctx.partition(), msg_ctx.offset())
    req_id = msg.request_id
    values = msg.list_of_values
    msg_count = msg.msg_counter

    max_val = max(values)

    q1_msg = Queue1Message(request_id=req_id, max_value=max_val, msg_counter=msg_count)

    logger.info(q1_msg.model_dump())

    # demonstration of support for asyncio
    await asyncio.gather(fun1(), fun2())

    # send the message to "redis_queue".
    # give it a delay of 0.25 seconds before becoming visible for consumption
    # "delay" is an RSMQ configuration https://github.com/mlasevich/PyRSMQ#quick-intro-to-rsmq
    out_message = [("redis_queue", q1_msg, {"delay": 0.25})]
    return out_message


if __name__ == "__main__":
    main()
