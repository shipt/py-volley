from typing import Any, List, Tuple

from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.logging import logger

eng = Engine(
    input_queue="comp_1",
    output_queues=["test_queue_plugin"],
    yaml_config_path="./example/volley_config.yml",
)


@eng.stream_app
def main(msg: Any) -> List[Tuple[str, ComponentMessage]]:
    """adds one to a value
    using dict as schema, which is essentially no schema
    """
    req_id = msg["request_id"]
    max_val = msg["max_value"]

    output_msg = ComponentMessage(request_id=req_id, max_plus_1=max_val + 1)

    logger.info(f"{req_id=}: {max_val=}")
    return [("test_queue_plugin", output_msg)]


if __name__ == "__main__":
    main()
