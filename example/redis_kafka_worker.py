import logging
from typing import List, Tuple

from example.data_models import InputMessage, RedisOutput
from volley import Engine

logging.basicConfig(level=logging.INFO)


queue_config = {
    "input-queue": {
        "value": "redis.input.queue",
        "profile": "rsmq",
        "data_model": "example.data_models.InputMessage",
    },
    "output-topic": {
        "value": "localhost.redis.kafka.output",
        "profile": "confluent",
        "data_model": "example.data_models.RedisOutput",
    },
}
redis_app = Engine(
    app_name="redis_to_kafka_example",
    input_queue="input-queue",
    output_queues=["output-topic"],
    queue_config=queue_config,
    metrics_port=None,
)

cnt = 0


@redis_app.stream_app
def main(msg: InputMessage) -> List[Tuple[str, RedisOutput]]:
    global cnt
    cnt += 1
    out_message = RedisOutput(request_id=msg.request_id, counter=cnt)
    return [("output-topic", out_message)]


if __name__ == "__main__":
    main()
