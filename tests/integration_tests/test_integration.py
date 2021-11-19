import json
import time
from typing import Dict, List
from uuid import uuid4

from pyshipt_streams import KafkaConsumer, KafkaProducer

from example.data_models import InputMessage
from volley.logging import logger
from volley.queues import Queue, available_queues


def test_end_to_end() -> None:  # noqa
    # get name of the input topic
    queues: Dict[str, Queue] = available_queues()
    produce_topic = queues["input-queue"].value
    logger.info(f"{produce_topic=}")
    p = KafkaProducer()

    # get some sample data
    data = InputMessage.schema()["examples"][0]

    # create some unique request id for tracking
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        data["request_id"] = req_id
        p.publish(produce_topic, value=json.dumps(data))
    p.flush()

    # consumer the messages off the output topic
    consume_topic = queues["output-queue"].value
    logger.info(f"{consume_topic=}")
    c = KafkaConsumer(consumer_group="int-test-group")
    c.subscribe([consume_topic])

    # wait some seconds max for messages to reach output topic
    start = time.time()
    consumed_messages = []
    while (time.time() - start) < 15:
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


def test_dead_letter_queue() -> None:
    queues: Dict[str, Queue] = available_queues()
    produce_topic = queues["input-queue"].value
    logger.info(f"{produce_topic=}")
    p = KafkaProducer()
    data = {"bad": "data"}

    # publish data to input-topic that does not meet schema requirements
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        data["request_id"] = req_id
        p.publish(produce_topic, value=json.dumps(data))
    p.flush()

    dlq_topic = queues["dead-letter-queue"].value
    logger.info(f"{dlq_topic=}")
    c = KafkaConsumer(consumer_group="int-test-group")
    c.subscribe([dlq_topic])

    start = time.time()
    consumed_messages = []
    while (time.time() - start) < 15:
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
        _id = m["request_id"]
        assert _id in request_ids
        conusumed_ids.append(_id)

    for _id in request_ids:
        # assert all ids we produced were in the list we consumed
        assert _id in conusumed_ids

    assert len(request_ids) == len(conusumed_ids)
