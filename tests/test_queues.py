from typing import Dict, List, Type, Union

import pytest

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.connectors.confluent import ConfluentKafkaConsumer, ConfluentKafkaProducer
from volley.connectors.rsmq import RSMQConsumer, RSMQProducer
from volley.data_models import GenericMessage
from volley.models.base import BaseModelHandler
from volley.models.pydantic_model import PydanticModelHandler
from volley.profiles import ConnectionType, Profile
from volley.queues import Queue, construct_queue_map
from volley.serializers.base import BaseSerialization
from volley.serializers.msgpack_serializer import MsgPackSerialization


def test_bad_connnect_type(confluent_consumer_profile: Profile) -> None:
    """config passed through to connector must be a dictionary"""
    q = Queue(
        name="test",
        value="long_value",
        profile=confluent_consumer_profile,
    )
    with pytest.raises(TypeError):
        q.connect("BAD_TYPE")  # type: ignore


def test_missing_queue_attr(confluent_consumer_profile: Profile, config_dict: Dict[str, Dict[str, str]]) -> None:
    del config_dict["input-topic"]["value"]
    pm = {"input-topic": confluent_consumer_profile}

    with pytest.raises(KeyError):
        construct_queue_map(profiles=pm, configs=config_dict)


def test_missing_producer(confluent_consumer_profile: Profile) -> None:
    """trying to connect the producer on a queue configured for consumer must raise"""
    confluent_consumer_profile.producer = None
    q = Queue(
        name="test",
        value="long_value",
        profile=confluent_consumer_profile,
    )
    with pytest.raises(ValueError):
        q.connect(ConnectionType.PRODUCER)


def test_missing_consumer(confluent_producer_profile: Profile) -> None:
    """trying to connect the consumer on a queue configured for producer must raise"""
    confluent_producer_profile.consumer = None
    q = Queue(
        name="test",
        value="long_value",
        profile=confluent_producer_profile,
    )
    with pytest.raises(ValueError):
        q.connect(ConnectionType.CONSUMER)


def test_valid_supported_queues(
    all_supported_producer_profiles: List[Profile], all_supported_consumer_profiles: List[Profile]
) -> None:
    """all profiles must be able to construct a valid Queue"""
    for profile in all_supported_producer_profiles + all_supported_consumer_profiles:
        Queue(name="test", value="test", profile=profile)


def test_invalid_supported_queues(
    all_supported_producer_profiles: List[Profile], all_supported_consumer_profiles: List[Profile]
) -> None:
    """a supported profile with bad string value should raise"""
    for profile in all_supported_producer_profiles + all_supported_consumer_profiles:
        profile.data_model = "bad.path.to.object"
        with pytest.raises(ImportError):
            Queue(name="test", value="test", profile=profile)


@pytest.mark.parametrize(
    "consumer,producer,data_model,model_handler,serializer,connection_type",
    [
        (
            ConfluentKafkaConsumer,
            "volley.connectors.confluent.ConfluentKafkaProducer",
            GenericMessage,
            PydanticModelHandler,
            "volley.serializers.msgpack_serializer.MsgPackSerialization",
            ConnectionType.PRODUCER,
        ),
        (
            ConfluentKafkaConsumer,
            "volley.connectors.confluent.ConfluentKafkaProducer",
            "volley.data_models.GenericMessage",
            PydanticModelHandler,
            "volley.serializers.msgpack_serializer.MsgPackSerialization",
            ConnectionType.CONSUMER,
        ),
        (
            RSMQConsumer,
            ConfluentKafkaProducer,
            GenericMessage,
            PydanticModelHandler,
            MsgPackSerialization,
            ConnectionType.PRODUCER,
        ),
        (
            ConfluentKafkaConsumer,
            RSMQProducer,
            GenericMessage,
            PydanticModelHandler,
            MsgPackSerialization,
            ConnectionType.CONSUMER,
        ),
    ],
)
def test_queue_from_module_profile(
    consumer: Union[str, Type[BaseConsumer]],
    producer: Union[str, Type[BaseProducer]],
    data_model: Union[str, type],
    model_handler: Union[str, Type[BaseModelHandler]],
    serializer: Union[str, Type[BaseSerialization]],
    connection_type: ConnectionType,
) -> None:
    """initialize profile using combination of dot path and object configurations"""
    profile = Profile(
        consumer=consumer,
        producer=producer,
        data_model=data_model,
        model_handler=model_handler,
        serializer=serializer,
        connection_type=connection_type,
    )
    queue = Queue(name="test", value="test", profile=profile)
    queue.connect(connection_type)

    if connection_type == ConnectionType.CONSUMER:
        assert isinstance(queue.consumer_con, BaseConsumer)
    else:
        assert isinstance(queue.producer_con, BaseProducer)

    assert isinstance(queue.data_model, type)
    assert isinstance(queue.model_handler, BaseModelHandler)
    assert isinstance(queue.serializer, BaseSerialization)
