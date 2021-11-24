from typing import List, Tuple

from example.data_models import Queue1Message, InputMessage, ComponentMessage, PostgresMessage
from volley.engine import Engine
from volley.logging import logger

eng = Engine(
    input_queue="input-topic",
    # output_queues=["redis_queue"],
    output_queues=["output-topic"],
    # output_queues=["redis_queue", "postgres_queue"],
    yaml_config_path="./example/volley_config.yml",
    dead_letter_queue="dead-letter-queue",
)


@eng.stream_app
def main(msg: InputMessage) -> List[Tuple[str, Queue1Message]]:

    req_id = msg.request_id
    values = msg.list_of_values
    logger.info(f"{req_id=}: {values=}")

    max_val = max(values)

    # q1_msg = Queue1Message(request_id=req_id, max_value=max_val)
    # return [("redis_queue", q1_msg)]

    output_msg = PostgresMessage(request_id=req_id, max_plus=max_val)
    return [
        ("postgres_queue", output_msg),
        ("redis_queue", q1_msg)
    ]

if __name__ == "__main__":
    main()
