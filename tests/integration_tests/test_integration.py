import json
import time
from threading import Thread
from typing import Any, Dict, List
from uuid import uuid4

import pytest
import redis
from confluent_kafka import OFFSET_END, Consumer, Producer, TopicPartition
from rsmq import RedisSMQ

from example.data_models import InputMessage
from example.kafka_kafka_worker import CONSUMER_GROUP
from example.kafka_kafka_worker import eng as kafka_kafka_eng
from example.kafka_kafka_worker import main as kafka_test_app
from example.redis_kafka_worker import main as redis_test_app
from example.redis_kafka_worker import redis_app as redis_kafka_eng
from tests.integration_tests.conftest import Environment
from volley.connectors import (
    ConfluentKafkaConsumer,
    ConfluentKafkaProducer,
    RSMQProducer,
)
from volley.data_models import QueueMessage
from volley.logging import logger

POLL_TIMEOUT = 30


def consume_messages(consumer: Consumer, num_expected: int, serialize: bool = True) -> List[Dict[str, Any]]:
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
    broker_config: Dict[str, str], environment: Environment, int_test_consumer: Consumer
) -> None:
    """offsets must commit properly
    publish some messages. consume them. commit offsets.
    """
    # ensure the consumer group starts at the high offset
    int_test_consumer.assign([TopicPartition(topic=environment.test_topic, partition=0, offset=OFFSET_END)])
    consumer = ConfluentKafkaConsumer(queue_name=environment.test_topic, config=broker_config, poll_interval=30)

    # send messages to test topic
    producer = Producer({"bootstrap.servers": environment.brokers})

    num_test_message = 3
    for i in range(num_test_message):
        producer.produce(topic=environment.test_topic, value=f"message_{i}".encode("utf-8"))
    producer.flush()

    # consume one message, record offset but do not commit it, leave consumer group
    message_0: QueueMessage = consumer.consume()  # type: ignore
    offset_0 = message_0.message_context.offset()
    consumer.shutdown()

    # recreate the consumer and subscribe
    consumer = ConfluentKafkaConsumer(queue_name=environment.test_topic, config=broker_config, poll_interval=30)
    # consume message again, must be same offset that we previously consumed
    message_0a: QueueMessage = consumer.consume()  # type: ignore
    assert message_0a.message_context.offset() == offset_0
    # commit the offset, leave the consumer group
    consumer.on_success(message_context=message_0a.message_context)
    consumer.shutdown()

    # recreate the consumer
    consumer = ConfluentKafkaConsumer(queue_name=environment.test_topic, config=broker_config, poll_interval=30)
    # consume message again, must be the next offset
    message_1: QueueMessage = consumer.consume()  # type: ignore
    offset_1 = message_1.message_context.offset()
    assert offset_1 == offset_0 + 1
    # commit the offset, leave the consumer group
    consumer.on_success(message_context=message_1.message_context)
    consumer.shutdown()

    # use Confluent consumer directly, validate offset is also the next offset
    int_test_consumer.subscribe([environment.test_topic])
    message_2 = int_test_consumer.poll(30)
    assert message_2.offset() == offset_1 + 1
    int_test_consumer.close()


@pytest.mark.integration
def test_confluent_async_consume(
    broker_config: Dict[str, str], environment: Environment, int_test_consumer: Consumer
) -> None:
    """offsets must commit properly
    publish some messages. consume them. commit offsets.
    """
    # ensure the consumer group starts at the high offset
    int_test_consumer.assign([TopicPartition(topic=environment.test_topic, partition=0, offset=OFFSET_END)])
    consumer1 = ConfluentKafkaConsumer(queue_name=environment.test_topic, config=broker_config, poll_interval=30)

    # send dummy messages to test topic
    producer0 = ConfluentKafkaProducer(
        queue_name=environment.test_topic,
        config={"bootstrap.servers": environment.brokers, "auto.commit.interval.ms": 500},
    )
    num_test_message = 3
    for i in range(num_test_message):
        producer0.produce(
            queue_name=environment.test_topic, message=f"message_{i}".encode("utf-8"), message_context=None
        )
    # do not call poll on this ^ producer. its just creating some test data

    # consume a mesage we just produced
    # consume one message, record offset but do not commit it
    message_0: QueueMessage = consumer1.consume()  # type: ignore
    offset_0 = message_0.message_context.offset()

    # init a new producer, use it to produce and acknowledge receipt of ^^ message consumed
    producer1 = ConfluentKafkaProducer(
        queue_name=environment.test_topic, config={"bootstrap.servers": environment.brokers}
    )
    # do not init the callbacks
    # should not have stored anything in local state
    assert consumer1.last_offset == {}
    producer1.produce(
        queue_name=environment.test_topic, message="message".encode("utf-8"), message_context=message_0.message_context
    )
    # poll before produce, will not produce a deliver report or change local state
    assert consumer1.last_offset == {}
    # init the callback poll
    producer1.init_callbacks(consumer=consumer1, thread=True)
    time.sleep(1)
    assert consumer1.last_offset[0] == offset_0
    producer1.produce(
        queue_name=environment.test_topic, message="message".encode("utf-8"), message_context=message_0.message_context
    )
    assert consumer1.last_offset[0] == offset_0
    # this will store offset in local state. it should also store_offsets() and commit to broker()
    # leave consumer group, shutdown producer
    consumer1.shutdown()
    producer1.shutdown()

    # recreate consumer. validate our offsets committed properly
    consumer2 = ConfluentKafkaConsumer(queue_name=environment.test_topic, config=broker_config, poll_interval=30)
    assert consumer2.last_offset == {}
    # consumer another message. our previous offsets should have been committed
    message_1: QueueMessage = consumer2.consume()  # type: ignore
    offset_1 = message_1.message_context.offset()
    assert offset_0 == offset_1 - 1

    # initialize the callbacks. these will auto trigger producer poll()
    producer2 = ConfluentKafkaProducer(
        queue_name=environment.test_topic, config={"bootstrap.servers": environment.brokers}
    )
    # should be no local state on the consumer yet
    assert consumer2.last_offset == {}
    # producing a message should
    producer2.produce(
        queue_name=environment.test_topic, message="message".encode("utf-8"), message_context=message_1.message_context
    )
    # producer will call poll(), but there should be no pending reports
    assert consumer2.last_offset == {}
    # init the callbacks
    producer2.init_callbacks(consumer=consumer2)
    # there is a delay, so wait. this will call poll and change local state
    time.sleep(1)
    assert consumer2.last_offset[0] == offset_1

    # close connections
    consumer2.shutdown()
    producer2.shutdown()
    # one final assertion on offset commits via callbacks
    consumer3 = ConfluentKafkaConsumer(queue_name=environment.test_topic, config=broker_config, poll_interval=30)
    message_2: QueueMessage = consumer3.consume()  # type: ignore
    offset_2 = message_2.message_context.offset()
    assert offset_1 == offset_2 - 1
    consumer3.shutdown()


@pytest.mark.integration
def test_kafka_kafka_worker(int_test_producer: Producer, int_test_consumer: Consumer, environment: Environment) -> None:
    """validate kafka w/ async commits are handled in a running app

    'kafka_kafka_worker' runs in its own thread, is listening to input_topic and publishing to output_topic

    This test will publish to input_topic, then listen to output_topic.
    - validates data in output topic is as expected
    - validates consumer group offsets committed to input partition as expected

    """
    input_topic = kafka_kafka_eng.queue_map[kafka_kafka_eng.input_queue].value
    output_topic = kafka_kafka_eng.queue_map[kafka_kafka_eng.output_queues[0]].value

    # subscribe to the topic kafka_kafka_worker will publish to
    int_test_consumer.assign([TopicPartition(topic=output_topic, partition=0, offset=OFFSET_END)])
    int_test_consumer.subscribe([output_topic])

    # start the example.kafka_kafka_worker.py service in a thread
    app_thread = Thread(target=kafka_test_app, daemon=True)
    app_thread.start()
    time.sleep(3)

    # get starting offset
    # this is the offset for kafka_kafka_worker on the input_topic partition 0
    # (single partition in the test topic)
    consumer = Consumer({"group.id": CONSUMER_GROUP, "bootstrap.servers": environment.brokers})
    _offset = consumer.committed([TopicPartition(input_topic, 0)])[0].offset
    if _offset < 0:
        starting_offset = 0
    else:
        starting_offset = _offset

    # create some unique request id for tracking
    test_messages = 3
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    data = InputMessage.schema()["examples"][0]
    for req_id in request_ids:
        # publish the messages
        data["request_id"] = req_id
        int_test_producer.produce(input_topic, value=json.dumps(data))
    int_test_producer.flush()

    time.sleep(2)

    logger.info("Closed thread")

    consumed_messages = consume_messages(int_test_consumer, num_expected=test_messages, serialize=True)

    kafka_kafka_eng.killer.kill_now = True
    app_thread.join()

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

    # validate the worker committed the offsets
    current_offset = consumer.committed([TopicPartition(input_topic, 0)])[0].offset
    assert current_offset == (starting_offset + test_messages)


@pytest.mark.integration
def test_redis_to_kafka(int_test_consumer: Consumer, environment: Environment) -> None:
    """consumes from redis, produce async to kafka, deletes w/ callback"""

    input = redis_kafka_eng.queue_map[redis_kafka_eng.input_queue].value
    output = redis_kafka_eng.queue_map[redis_kafka_eng.output_queues[0]].value

    assert redis_kafka_eng.killer.kill_now is False

    # subscribe the topic the app will publish to
    int_test_consumer.assign([TopicPartition(topic=output, partition=0, offset=OFFSET_END)])
    int_test_consumer.subscribe([output])

    r = redis.Redis(host=environment.redis_host)

    # make sure the queue is empty
    queue = RedisSMQ(host=environment.redis_host, qname=input)
    queue.deleteQueue().exceptions(False).execute()

    _producer = RSMQProducer(host=environment.redis_host, queue_name=input)

    # start redis_kafka_worker in thread
    app_thread = Thread(target=redis_test_app, daemon=True)
    app_thread.start()
    time.sleep(3)

    # add some data to the input rsmq
    test_messages = 5
    request_ids: List[str] = [f"test_{x}_{str(uuid4())[:5]}" for x in range(test_messages)]
    data = InputMessage.schema()["examples"][0]
    for req_id in request_ids:
        data["request_id"] = req_id
        _producer.produce(queue_name=input, message=json.dumps(data).encode("utf-8"))

    consumed_messages = consume_messages(int_test_consumer, num_expected=test_messages, serialize=True)

    # shut down the app in thread
    redis_kafka_eng.killer.kill_now = True
    app_thread.join()

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

    # all messages should have been deleted
    assert r.zcard(f"rsmq:{input}") == 0
