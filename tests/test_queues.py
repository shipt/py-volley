from typing import Dict, List

import pytest

from volley.profiles import ConnectionType, Profile
from volley.queues import Queue, construct_queue_map


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
