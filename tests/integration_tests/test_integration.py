import json
import time
from typing import Any, List
from uuid import uuid4

import pytest
from confluent_kafka import OFFSET_END, Consumer, Producer, TopicPartition

from example.data_models import InputMessage
from tests.integration_tests.conftest import Environment
from volley.connectors import ConfluentKafkaConsumer, ConfluentKafkaProducer
from volley.data_models import QueueMessage
from volley.logging import logger

POLL_TIMEOUT = 30


def consume_messages(consumer: Consumer, num_expected: int, serialize: bool = True) -> List[dict[str, Any]]:
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


@pytest.mark.integration
def test_end_to_end(int_test_producer: Producer, int_test_consumer: Consumer, environment: Environment) -> None:  # noqa
    """good data should make it all the way through app"""
    # get name of the input topic
    logger.info(f"{environment.input_topic=}")

    # get some sample data
    data = InputMessage.schema()["examples"][0]

    # consumer the messages off the output topic
    consume_topic = environment.output_topic
    logger.info(f"{consume_topic=}")

    int_test_consumer.assign([TopicPartition(topic=consume_topic, partition=0, offset=OFFSET_END)])
    int_test_consumer.subscribe([consume_topic])

    # create some unique request id for tracking
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        data["request_id"] = req_id
        int_test_producer.produce(environment.input_topic, value=json.dumps(data))
    int_test_producer.flush()

    consumed_messages = consume_messages(consumer=int_test_consumer, num_expected=len(request_ids))
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


@pytest.mark.integration
def test_dlq_schema_violation(
    int_test_producer: Producer, int_test_consumer: Consumer, environment: Environment
) -> None:
    """publish bad data to input queue
    it should cause schema violation and end up on DLQ
    """
    logger.info(f"{environment.input_topic=}")
    data = {"bad": "data"}
    logger.info(f"{environment.dlq=}")
    int_test_consumer.assign([TopicPartition(topic=environment.dlq, partition=0, offset=OFFSET_END)])
    int_test_consumer.subscribe([environment.dlq])

    # publish data to input-topic that does not meet schema requirements
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        data["request_id"] = req_id
        int_test_producer.produce(environment.input_topic, value=json.dumps(data))
    int_test_producer.flush()

    consumed_messages = []
    consumed_messages = consume_messages(consumer=int_test_consumer, num_expected=len(request_ids))

    conusumed_ids = []
    for m in consumed_messages:
        # assert all consumed IDs were from the list we produced
        _id = m["request_id"]
        assert _id in request_ids
        conusumed_ids.append(_id)

    logger.info(f"{conusumed_ids=}")
    for _id in request_ids:
        # assert all ids we produced were in the list we consumed
        logger.info(f"id={_id}")
        assert _id in conusumed_ids

    assert len(request_ids) == len(conusumed_ids)


@pytest.mark.integration
def test_dlq_serialization_failure(
    int_test_producer: Producer, int_test_consumer: Consumer, environment: Environment
) -> None:
    """publish malformed json to input queue
    expect serialization failure and successful publish to the DLQ
    """
    logger.info(f"{environment.input_topic=}")
    # message missing closing quote on the key
    data = """{"malformed:"json"}"""

    logger.info(f"{environment.dlq=}")
    int_test_consumer.assign([TopicPartition(topic=environment.dlq, partition=0, offset=OFFSET_END)])
    int_test_consumer.subscribe([environment.dlq])

    # publish data to input-topic that does not meet schema requirements
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    for req_id in request_ids:
        # publish the messages
        _d = data + req_id
        # data is just an extremely messy byte string
        int_test_producer.produce(environment.input_topic, value=_d.encode("utf-8"))
    int_test_producer.flush()

    # dont try to serialize - we already know it will fail serialization
    consumed_messages = consume_messages(consumer=int_test_consumer, num_expected=len(request_ids), serialize=False)

    conusumed_ids = []
    for m in consumed_messages:
        # assert all consumed IDs were from the list we produced
        _id = str(m).split("}")[-1]
        conusumed_ids.append(_id)

    for _id in request_ids:
        # assert all ids we produced were in the list we consumed
        assert _id in conusumed_ids

    assert len(request_ids) == len(conusumed_ids)


@pytest.mark.integration
def test_confluent_consume(
    broker_config: dict[str, str], environment: Environment, int_test_consumer: Consumer
) -> None:
    """offsets must commit properly
    publish some messages. consume them. commit offsets.
    """
    # ensure the consumer group starts at the high offset
    int_test_consumer.assign([TopicPartition(topic=environment.test_topic, partition=0, offset=OFFSET_END)])
    consumer = ConfluentKafkaConsumer(queue_name=environment.test_topic, config=broker_config, poll_interval=30)

    # send messages to test topic
    producer = ConfluentKafkaProducer(
        queue_name=environment.test_topic, config={"bootstrap.servers": environment.brokers}
    )
    num_test_message = 3
    for i in range(num_test_message):
        producer.produce(queue_name=environment.test_topic, message=f"message_{i}".encode("utf-8"))
    producer.shutdown()

    # consume one message, record offset but do not commit it, leave consumer group
    message_0: QueueMessage = consumer.consume(queue_name=environment.test_topic)  # type: ignore
    offset_0 = message_0.message_context.offset()
    consumer.shutdown()

    # recreate the consumer and subscribe
    consumer = ConfluentKafkaConsumer(queue_name=environment.test_topic, config=broker_config, poll_interval=30)
    # consume message again, must be same offset that we previously consumed
    message_0a: QueueMessage = consumer.consume(queue_name=environment.test_topic)  # type: ignore
    assert message_0a.message_context.offset() == offset_0
    # commit the offset, leave the consumer group
    consumer.delete_message(message_context=message_0a.message_context, queue_name=environment.test_topic)
    consumer.shutdown()

    # recreate the consumer
    consumer = ConfluentKafkaConsumer(queue_name=environment.test_topic, config=broker_config, poll_interval=30)
    # consume message again, must be the next offset
    message_1: QueueMessage = consumer.consume(queue_name=environment.test_topic)  # type: ignore
    offset_1 = message_1.message_context.offset()
    assert offset_1 == offset_0 + 1
    # commit the offset, leave the consumer group
    consumer.delete_message(message_context=message_1.message_context, queue_name=environment.test_topic)
    consumer.shutdown()

    # use Confluent consumer directly, validate offset is also the next offset
    int_test_consumer.subscribe([environment.test_topic])
    message_2 = int_test_consumer.poll(30)
    assert message_2.offset() == offset_1 + 1
    int_test_consumer.close()
