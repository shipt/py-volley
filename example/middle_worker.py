from random import randint
from typing import Any, List, Tuple

from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.logging import logger

eng = Engine(
    input_queue="redis_queue",
    output_queues=["postgres_queue", "output-topic"],
    yaml_config_path="./example/volley_config.yml",
)


@eng.stream_app
def main(msg: Any) -> List[Tuple[str, ComponentMessage]]:
    """adds one to a value
    using dict as schema, which provides no schema validation
    """
    req_id = msg["request_id"]
    max_val = msg["max_value"]

    max_plus_jiggle = max_val + randint(1, 20)

    output_msg = ComponentMessage(request_id=req_id, max_plus=max_plus_jiggle)

    logger.info(f"{req_id=}: {max_val=}")
    return [("postgres_queue", output_msg), ("output-topic", output_msg)]


if __name__ == "__main__":
    main()
