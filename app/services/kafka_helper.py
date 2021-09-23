import json
import os
from dataclasses import dataclass, field

import rollbar
from confluent_kafka import Producer
from loguru import logger


@dataclass
class KafkaProducer:
    producer: Producer = field(init=False, default=Producer({}))

    def __post_init__(self) -> None:
        try:
            conf = {
                "bootstrap.servers": os.getenv("KAFKA_BROKERS"),
                "security.protocol": "SASL_SSL",
                "sasl.username": os.getenv("KAFKA_KEY"),
                "sasl.password": os.getenv("KAFKA_SECRET"),
                "sasl.mechanism": "PLAIN",
            }
            # Create Producer instance
            self.producer = Producer(conf)
            logger.info("Connected to Kafka Broker")
        except Exception as e:
            rollbar.report_message(f"Could not connect to Kafka broker due to: {e}")

    def acked(self, err, msg) -> None:
        if err is not None:
            print(f"Failed to deliver message: {msg}: {err}")
        else:
            print(f"Message produced: {msg}")

    def add_message_to_kafka(self, topic: str, value: dict) -> None:
        try:
            self.producer.produce(topic=topic, value=json.dumps(value), callback=self.acked)
            logger.info(f"sent to topic: {topic}")
            self.producer.poll(0)
        except Exception as e:
            rollbar.report_message(f"Could not send message to Kafka due to: {e}")

    def kafka_flush(self) -> None:
        self.producer.flush()
