import json
import time
from typing import Dict, List
from uuid import uuid4

from confluent_kafka import OFFSET_END, TopicPartition
from pyshipt_streams import KafkaConsumer, KafkaProducer

from example.data_models import InputMessage
from tests.integration_tests.conftest import Environment
from volley.logging import logger
from volley.queues import Queue, available_queues

POLL_TIMEOUT = 30


def test_end_to_end(environment: Environment) -> None:  # noqa
    """good data should make it all the way through app"""
    # get name of the input topic
    logger.info(f"{environment.input_topic=}")
    p = KafkaProducer()

    # get some sample data
    data = InputMessage.schema()["examples"][0]

    # consumer the messages off the output topic
    consume_topic = environment.output_topic
    logger.info(f"{consume_topic=}")
    c = KafkaConsumer(consumer_group="int-test-group")
    c.consumer.assign([TopicPartition(topic=consume_topic, partition=0, offset=OFFSET_END)])
    c.subscribe([consume_topic])

    # create some unique request id for tracking
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        data["request_id"] = req_id
        p.publish(environment.input_topic, value=json.dumps(data))
    p.flush()

    # wait some seconds max for messages to reach output topic
    start = time.time()
    consumed_messages = []
    while (time.time() - start) < POLL_TIMEOUT:
        message = c.poll(1)
        if message is None:
            continue
        if message.error():
            logger.error(message.error())
        else:
            consumed_messages.append(json.loads(message.value().decode("utf-8")))

        if len(consumed_messages) == len(request_ids):
            break

    c.close()

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


def test_dead_letter_queue(environment: Environment) -> None:
    """publish bad data to input queue
    it should cause schema violation and end up on DLQ
    """
    logger.info(f"{environment.input_topic=}")
    p = KafkaProducer()
    data = {"bad": "data"}

    logger.info(f"{environment.dlq=}")
    c = KafkaConsumer(consumer_group="int-test-group")
    c.consumer.assign([TopicPartition(topic=environment.dlq, partition=0, offset=OFFSET_END)])
    c.subscribe([environment.dlq])

    # publish data to input-topic that does not meet schema requirements
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        data["request_id"] = req_id
        p.publish(environment.input_topic, value=json.dumps(data))
    p.flush()

    start = time.time()
    consumed_messages = []
    while (time.time() - start) < POLL_TIMEOUT:
        message = c.poll(1)
        if message is None:
            continue
        if message.error():
            logger.error(message.error())
        else:
            consumed_messages.append(json.loads(message.value().decode("utf-8")))
            if len(request_ids) == len(consumed_messages):
                break
    c.close()

    conusumed_ids = []
    for m in consumed_messages:
        # assert all consumed IDs were from the list we produced
        logger.info("#########")
        logger.info(m)
        _id = m["request_id"]
        assert _id in request_ids
        conusumed_ids.append(_id)

    for _id in request_ids:
        # assert all ids we produced were in the list we consumed
        assert _id in conusumed_ids

    assert len(request_ids) == len(conusumed_ids)
