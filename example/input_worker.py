import asyncio
import logging
import time
from typing import Any, List, Tuple

from example.data_models import InputMessage, Queue1Message
from volley.engine import Engine
from volley.logging import logger

logging.basicConfig(level=logging.INFO)

eng = Engine(
    input_queue="input-topic",
    output_queues=["redis_queue"],
    yaml_config_path="./example/volley_config.yml",
    dead_letter_queue="dead-letter-queue",
)


async def run_parallel(*functions: Any) -> None:
    await asyncio.gather(*functions)


async def fun1() -> None:
    time.sleep(2)
    logger.info("one")


async def fun2() -> None:
    time.sleep(2)
    logger.info("two")


@eng.stream_app
async def main(msg: InputMessage) -> List[Tuple[str, Queue1Message, dict[str, float]]]:

    req_id = msg.request_id
    values = msg.list_of_values
    msg_count = msg.msg_counter

    max_val = max(values)

    q1_msg = Queue1Message(request_id=req_id, max_value=max_val, msg_counter=msg_count)

    logger.info(q1_msg.dict())

    await run_parallel(fun1(), fun2())

    # send the message to "redis_queue".
    # give it a delay of 0.25 seconds before becoming visibilty for consumption
    out_message = [("redis_queue", q1_msg, {"delay": 0.25})]
    return out_message


if __name__ == "__main__":
    main()
