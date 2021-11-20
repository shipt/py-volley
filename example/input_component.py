from typing import List, Tuple

from example.data_models import Comp1Message, InputMessage
from volley.engine import Engine
from volley.logging import logger

eng = Engine(
    input_queue="input-queue",
    output_queues=["comp_1"],
    yaml_config_path="./example/volley_config.yml",
    dead_letter_queue="dead-letter-queue",
)


@eng.stream_app
def main(msg: InputMessage) -> List[Tuple[str, Comp1Message]]:

    req_id = msg.request_id
    values = msg.list_of_values

    max_val = max(values)

    output_msg = Comp1Message(request_id=req_id, max_value=max_val)

    logger.info(f"{req_id=}: {values=}")

    return [("comp_1", output_msg)]


if __name__ == "__main__":
    main()
