import json

from confluent_kafka import Producer

producer = Producer({"bootstrap.servers": "localhost:9092"})
producer.produce(topic="my.kafka.topic.name", value=json.dumps({"my_values": [1, 2, 3]}))
producer.flush(10)
