from typing import List, Tuple

from example.data_models import Queue1Message, InputMessage, ComponentMessage
from volley.engine import Engine
from volley.logging import logger

eng = Engine(
    input_queue="input-topic",
    output_queues=["queue_1"],
    # output_queues=["output-topic", "queue_2"],
    yaml_config_path="./example/volley_config.yml",
    dead_letter_queue="dead-letter-queue",
)


@eng.stream_app
def main(msg: InputMessage) -> List[Tuple[str, Queue1Message]]:

    req_id = msg.request_id
    values = msg.list_of_values
    logger.info(f"{req_id=}: {values=}")

    max_val = max(values)

    output_msg = Queue1Message(request_id=req_id, max_value=max_val)
    return [("queue_1", output_msg)]

    # output_msg = ComponentMessage(request_id=req_id, max_plus=max_val)
    # return [
    #     ("queue_2", output_msg),
    #     ("output-topic", output_msg)
    # ]

if __name__ == "__main__":
    main()
