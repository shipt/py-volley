import json
import time
from typing import Any, List
from uuid import uuid4

from confluent_kafka import OFFSET_END
from confluent_kafka import Consumer as KafkaConsumer
from confluent_kafka import Producer as KafkaProducer
from confluent_kafka import TopicPartition

from example.data_models import InputMessage
from tests.integration_tests.conftest import Environment
from volley.logging import logger

POLL_TIMEOUT = 30


def consume_messages(consumer: KafkaConsumer, num_expected: int, serialize: bool = True) -> List[dict[str, Any]]:
    """helper function for polling 'everything' off a topic"""
    start = time.time()
    consumed_messages = []
    while (time.time() - start) < POLL_TIMEOUT:
        message = consumer.poll(1)
        if message is None:
            continue
        if message.error():
            logger.error(message.error())
        else:
            _msg = message.value().decode("utf-8")
            if serialize:
                msg = json.loads(_msg)
            else:
                msg = _msg
            consumed_messages.append(msg)
            if num_expected == len(consumed_messages):
                break
    consumer.close()
    return consumed_messages


def test_end_to_end(environment: Environment) -> None:  # noqa
    """good data should make it all the way through app"""
    # get name of the input topic
    logger.info(f"{environment.input_topic=}")
    producer_conf = {"bootstrap.servers": environment.brokers}
    p = KafkaProducer(producer_conf)

    # get some sample data
    data = InputMessage.schema()["examples"][0]

    # consumer the messages off the output topic
    consume_topic = environment.output_topic
    logger.info(f"{consume_topic=}")
    consumer_conf = {"group.id": "int-test-topic"}
    c = KafkaConsumer(consumer_conf)
    c.assign([TopicPartition(topic=consume_topic, partition=0, offset=OFFSET_END)])
    c.subscribe([consume_topic])

    # create some unique request id for tracking
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        data["request_id"] = req_id
        p.produce(environment.input_topic, value=json.dumps(data))
    p.flush()

    consumed_messages = consume_messages(consumer=c, num_expected=len(request_ids))
    conusumed_ids = []
    for m in consumed_messages:
        # assert all consumed IDs were from the list we produced
        _id = m["request_id"]
        assert _id in request_ids
        conusumed_ids.append(_id)

    for _id in request_ids:
        # assert all ids we produced were in the list we consumed
        assert _id in conusumed_ids

    assert len(request_ids) == len(conusumed_ids)


def test_dlq_schema_violation(environment: Environment) -> None:
    """publish bad data to input queue
    it should cause schema violation and end up on DLQ
    """
    logger.info(f"{environment.input_topic=}")
    producer_conf = {"bootstrap.servers": environment.brokers}
    p = KafkaProducer(producer_conf)
    data = {"bad": "data"}

    logger.info(f"{environment.dlq=}")
    consumer_conf = {"group.id": "int-test-group"}
    c = KafkaConsumer(consumer_conf)
    c.assign([TopicPartition(topic=environment.dlq, partition=0, offset=OFFSET_END)])
    c.subscribe([environment.dlq])

    # publish data to input-topic that does not meet schema requirements
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        data["request_id"] = req_id
        p.produce(environment.input_topic, value=json.dumps(data))
    p.flush()

    consumed_messages = []
    consumed_messages = consume_messages(consumer=c, num_expected=len(request_ids))

    conusumed_ids = []
    for m in consumed_messages:
        # assert all consumed IDs were from the list we produced
        _id = m["request_id"]
        assert _id in request_ids
        conusumed_ids.append(_id)

    for _id in request_ids:
        # assert all ids we produced were in the list we consumed
        assert _id in conusumed_ids

    assert len(request_ids) == len(conusumed_ids)


def test_dlq_serialization_failure(environment: Environment) -> None:
    """publish malformed json to input queue
    expect serialization failure and successful publish to the DLQ
    """
    logger.info(f"{environment.input_topic=}")
    producer_conf = {"bootstrap.servers": environment.brokers}
    p = KafkaProducer(producer_conf)

    # message missing closing quote on the key
    data = """{"malformed:"json"}"""

    logger.info(f"{environment.dlq=}")
    consumer_conf = {"group.id": "int-test-group"}
    c = KafkaConsumer(consumer_conf)
    c.assign([TopicPartition(topic=environment.dlq, partition=0, offset=OFFSET_END)])
    c.subscribe([environment.dlq])

    # publish data to input-topic that does not meet schema requirements
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        _d = data + req_id
        # data is just an extremely messy byte string
        p.produce(environment.input_topic, value=_d.encode("utf-8"))
    p.flush()

    # dont try to serialize - we already know it will fail serialization
    consumed_messages = consume_messages(consumer=c, num_expected=len(request_ids), serialize=False)

    conusumed_ids = []
    for m in consumed_messages:
        # assert all consumed IDs were from the list we produced
        _id = str(m).split("}")[-1]
        conusumed_ids.append(_id)

    for _id in request_ids:
        # assert all ids we produced were in the list we consumed
        assert _id in conusumed_ids

    assert len(request_ids) == len(conusumed_ids)
