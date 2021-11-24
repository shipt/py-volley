from random import randint
from typing import Any, List, Tuple

from example.data_models import OutputMessage, PostgresMessage
from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.logging import logger

queue_config = {
    # define queue configurations in a dict
    # overrwrites any existing yaml configs
    "redis_queue": {
        "value": "long_name_1",
        "type": "rsmq",
        "schema": "dict",
        "producer": "example.plugins.my_plugin.MyPGProducer",
        "consumer": "example.plugins.my_plugin.MyPGConsumer",
    },
    "postgres_queue": {
        "value": "my_long_table_name",
        "type": "postgres",
        "schema": "example.data_models.PostgresMessage",
        # disable serializer - sqlachemy implementation in example/plugin/my_plugin.py handles this
        "serializer": "disabled",
        "producer": "example.plugins.my_plugin.MyPGProducer",
        "consumer": "example.plugins.my_plugin.MyPGConsumer",
    },
    "output-topic": {
        "value": "localhost.kafka.output",
        "type": "kafka",
        "schema": "example.data_models.OutputMessage",
    },
}

eng = Engine(input_queue="redis_queue", output_queues=["postgres_queue", "output-topic"], queue_config=queue_config)


@eng.stream_app
def main(msg: Any) -> List[Tuple[str, ComponentMessage]]:
    """adds one to a value
    using dict as schema, which provides no schema validation
    """
    req_id = msg["request_id"]
    max_val = msg["max_value"]

    max_plus_jiggle = max_val + randint(1, 20)

    output_msg = OutputMessage(request_id=req_id, max_plus=max_plus_jiggle)
    pg_msg = PostgresMessage(request_id=req_id, max_plus=max_plus_jiggle)

    logger.info(output_msg.dict())
    logger.info(pg_msg.dict())
    return [("postgres_queue", pg_msg), ("output-topic", output_msg)]


if __name__ == "__main__":
    main()
