import json
import os

from confluent_kafka import Message, Producer


def acked(err: str, msg: Message) -> None:
    if err is not None:
        print(
            f"Failed delivery to {msg.topic()}, message: {msg.value()}, error: {err}",
        )
    else:
        print(f"Successful delivery to {msg.topic()}, partion: {msg.partition()}, offset: {msg.offset()}")


producer = Producer({"bootstrap.servers": os.getenv("KAFKA_BROKERS", "localhost:9092")})
producer.produce(topic="my.kafka.topic.name", value=json.dumps({"my_values": [1, 2, 3]}), callback=acked)
producer.flush(10)
print("Published single message")
