import time
from typing import List, Optional, Tuple

from example.data_models import OutputMessage
from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.logging import logger

eng = Engine(
    input_queue="test_queue_plugin",
    output_queues=["output-queue"],
)

@eng.stream_app
def main(msg: ComponentMessage) -> Optional[List[Tuple[str, ComponentMessage]]]:
    if msg.results:  # type: ignore
        req_id = msg.results[0]["request_id"]  # type: ignore
        max_plus_1 = msg.results[0]["max_plus_1"]  # type: ignore

        output_msg = OutputMessage(request_id=req_id, max_plus_1=max_plus_1)

        logger.info(f"{req_id=}: {max_plus_1=}")
        return [("output-queue", output_msg)]
    else:
        time.sleep(1)
        return None


if __name__ == "__main__":
    main()
