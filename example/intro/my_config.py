# my_config.py
from typing import List

from pydantic import BaseModel


# define the schemas for the first and second worker nodes.
class InputMessage(BaseModel):
    my_values: List[float]


class OutputMessage(BaseModel):
    the_max: float


# define the configurations for the two queues, one in Kafka and the other in Redis.
queue_config = {
    "my-kafka-input": {
        "value": "my.kafka.topic.name",
        "profile": "confluent",
        "data_model": "my_config.InputMessage",
        "config": {"bootstrap.servers": "localhost:9092", "group.id": "my.consumer.group"},
    },
    "my-redis-output": {
        "value": "my.redis.output.queue.name",
        "data_model": "my_config.OutputMessage",
        "profile": "rsmq",
        "config": {
            "host": "localhost",
            "port": 6379,
        },
    },
}
