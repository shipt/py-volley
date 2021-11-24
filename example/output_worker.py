import time
from typing import List, Optional, Tuple

from example.data_models import OutputMessage
from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.logging import logger

# define queue configurations in a dict
# overrwrites any existing yaml configs
queue_config = {
    "postgres_queue": {
        "value": "longer_name",
        "type": "postgres",
        "serializer": "disabled",
        "schema": "volley.data_models.ComponentMessage",
        "producer": "example.plugins.my_plugin.MyPGProducer",
        "consumer": "example.plugins.my_plugin.MyPGConsumer",
    },
    "output-topic": {
        "value": "localhost.kafka.output",
        "type": "kafka",
        "schema": "volley.data_models.ComponentMessage",
    },
}

eng = Engine(input_queue="queue_2", output_queues=["output-topic"], queue_config=queue_config)


@eng.stream_app
def main(msg: ComponentMessage) -> Optional[List[Tuple[str, ComponentMessage]]]:
    if msg.results:  # type: ignore
        req_id = msg.results[0]["request_id"]  # type: ignore
        max_plus = msg.results[0]["max_plus"]  # type: ignore

        output_msg = OutputMessage(request_id=req_id, max_plus=max_plus)

        logger.info(f"{req_id=}: {max_plus=}")
        return [("postgres_queue", output_msg)]
    else:
        time.sleep(1)
        return None


if __name__ == "__main__":
    main()
