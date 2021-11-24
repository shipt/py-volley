from typing import List, Tuple

from example.data_models import InputMessage, PostgresMessage, Queue1Message
from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.logging import logger

eng = Engine(
    input_queue="input-topic",
    output_queues=["redis_queue"],
    yaml_config_path="./example/volley_config.yml",
    dead_letter_queue="dead-letter-queue",
)


@eng.stream_app
def main(msg: InputMessage) -> List[Tuple[str, ComponentMessage]]:

    req_id = msg.request_id
    values = msg.list_of_values

    max_val = max(values)

    q1_msg = Queue1Message(request_id=req_id, max_value=max_val)

    logger.info(q1_msg.dict())
    return [("redis_queue", q1_msg)]


if __name__ == "__main__":
    main()
