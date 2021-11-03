import json
import time
from typing import List
from uuid import uuid4

from pyshipt_streams import KafkaConsumer, KafkaProducer

from components.data_models import InputMessage
from core.logging import logger
from engine.queues import available_queues


def test_end_to_end() -> None:
    # get name of the input topic
    queues = available_queues()
    produce_topic = queues.queues["input-queue"].value
    logger.info(f"{produce_topic=}")
    p = KafkaProducer()

    # get some sample test data
    data = InputMessage.schema()["examples"][0]

    # create some unique request id for tracking
    test_messages = 5
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        data["bundle_request_id"] = req_id
        p.publish(produce_topic, value=json.dumps(data))
    # wait a second for synch
    time.sleep(1)
    # consumer the messages off the output topic
    consume_topic = queues.queues["output-queue"].value
    logger.info(f"{consume_topic=}")
    c = KafkaConsumer(consumer_group="int-test-group")
    c.subscribe([consume_topic])

    # wait 30 seconds max for messages to reach output topic
    start = time.time()
    consumed_messages = []
    while (time.time() - start) < 30:
        message = c.poll(0.25)
        if message is None:
            continue
        if message.error():
            logger.error(message.error())
        else:
            consumed_messages.append(json.loads(message.value().decode("utf-8")))

    conusumed_ids = []
    for m in consumed_messages:
        # assert all consumed IDs were from the list we produced
        _id = m["bundle_request_id"]
        assert _id in request_ids
        conusumed_ids.append(_id)

    for _id in request_ids:
        # assert all ids we produced were in the list we consumed
        assert _id in conusumed_ids

    assert len(request_ids) == len(conusumed_ids)
