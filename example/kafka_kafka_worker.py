import logging
from typing import List, Tuple

from example.data_models import InputMessage, KafkaKafkaOutput
from volley import Engine

logging.basicConfig(level=logging.INFO)

CONSUMER_GROUP = "kafka.kafka.worker"
INPUT_TOPIC = "localhost.kafka.kafka.input"
OUTPUT_TOPIC = "localhost.kafka.kafka.output"

queue_config = {
    "input-topic": {
        "value": INPUT_TOPIC,
        "profile": "confluent",
        "data_model": InputMessage,
        "config": {"group.id": CONSUMER_GROUP},
    },
    "output-topic": {
        "value": OUTPUT_TOPIC,
        "profile": "confluent",
        "data_model": KafkaKafkaOutput,
    },
    "dead-letter-queue": {
        "value": "localhost.kafka.kafka.dlq",
        "profile": "confluent-dlq",
    },
}
eng = Engine(
    app_name="kafka_to_kafka_example",
    input_queue="input-topic",
    output_queues=["output-topic"],
    queue_config=queue_config,
    dead_letter_queue="dead-letter-queue",
    metrics_port=None,
)

cnt = 0


@eng.stream_app
def main(msg: InputMessage) -> List[Tuple[str, KafkaKafkaOutput]]:
    global cnt
    cnt += 1
    out_message = KafkaKafkaOutput(request_id=msg.request_id, counter=cnt)
    return [("output-topic", out_message)]


if __name__ == "__main__":
    main()
