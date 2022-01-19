import asyncio
import logging
import time
from typing import List, Tuple

from example.data_models import InputMessage, Queue1Message
from volley import Engine
from volley.logging import logger

logging.basicConfig(level=logging.INFO)

eng = Engine(
    input_queue="input-topic",
    output_queues=["output-topic"],
    yaml_config_path="./example/volley_config.yml",
    dead_letter_queue="dead-letter-queue",
)


async def fun1() -> None:
    time.sleep(0.5)
    logger.info("one")


async def fun2() -> None:
    time.sleep(0.5)
    logger.info("two")


@eng.stream_app
async def main(msg: InputMessage) -> List[Tuple[str, Queue1Message, dict[str, float]]]:

    req_id = msg.request_id
    values = msg.list_of_values
    msg_count = msg.msg_counter

    max_val = max(values)

    q1_msg = Queue1Message(request_id=req_id, max_value=max_val, msg_counter=msg_count)

    logger.info(q1_msg.dict())

    # demonstration of support for asyncio
    await asyncio.gather(fun1(), fun2())

    # send the message to "redis_queue".
    # give it a delay of 0.25 seconds before becoming visible for consumption
    # "delay" is an RSMQ configuration https://github.com/mlasevich/PyRSMQ#quick-intro-to-rsmq
    out_message = [("output-topic", q1_msg, {"delay": 0.25})]
    return out_message


if __name__ == "__main__":
    main()
