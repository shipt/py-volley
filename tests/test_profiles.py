from typing import Any, Dict
from uuid import uuid4

import pytest
from pydantic import ValidationError

from volley import Engine
from volley.config import get_configs
from volley.profiles import ConnectionType, Profile, construct_profiles


def test_non_exist_profile() -> None:
    """requesting a non existent profile should fail"""
    non_exist_profile = f"non_exist_{str(uuid4())}"
    invalid = {"rando_queue": {"profile": non_exist_profile, "connection_type": ConnectionType.PRODUCER}}
    with pytest.raises(ValueError) as err:
        construct_profiles(invalid)

    assert non_exist_profile in str(err.value)


def test_non_exist_profile_init(config_dict: dict[str, dict[str, Any]]) -> None:
    """requesting a non existent profile should fail on init too"""
    non_exist_profile = f"non_exist_{str(uuid4())}"
    config_dict["input-topic"]["profile"] = non_exist_profile

    with pytest.raises(ValueError) as err:
        Engine(input_queue="input-topic", metrics_port=None, queue_config=config_dict)

    assert non_exist_profile in str(err.value)


def test_construct_producer_profiles() -> None:
    """verify all supported configurations are valid producer"""
    all_profiles = get_configs()["profiles"]
    for p, p_config in all_profiles.items():
        p_config["connection_type"] = ConnectionType.PRODUCER
    profile_map: Dict[str, Profile] = construct_profiles(all_profiles)

    for p, profile in profile_map.items():
        assert isinstance(p, str)
        assert p in all_profiles
        assert isinstance(profile, Profile)


def test_construct_consumer_profiles() -> None:
    """verify all supported configurations are valid consumers"""
    all_profiles = get_configs()["profiles"]
    for p, p_config in all_profiles.items():
        p_config["connection_type"] = ConnectionType.CONSUMER
    profile_map: Dict[str, Profile] = construct_profiles(all_profiles)

    for p, profile in profile_map.items():
        assert isinstance(p, str)
        assert p in all_profiles
        assert isinstance(profile, Profile)


def test_load_named_profiles(config_dict: dict[str, dict[str, Any]]) -> None:
    """use config_dict test fixture to validate loading of named profiles
    fixture specifies several named configurations, including DLQ
    """
    # get names of all supported profiles
    for _, cfg in config_dict.items():
        # connection_type is added by Engine()
        cfg["connection_type"] = ConnectionType.CONSUMER
    profile = construct_profiles(config_dict)
    for name, p in profile.items():
        if "dead-letter-queue" not in name:
            assert p.model_handler is not None
            assert p.data_model is not None
        else:
            assert p.model_handler is None
            assert p.data_model is None
            assert p.serializer is None


def test_all_supported_profiles() -> None:
    """all the profiles defined in Volley must be valid"""
    profiles = get_configs()["profiles"]
    for _, profile in profiles.items():
        profile["connection_type"] = ConnectionType.CONSUMER
        Profile(**profile)


def test_invalid_producer(confluent_producer_profile: Profile) -> None:
    """a producer without a producer connector should fail"""
    prod = confluent_producer_profile.dict()
    del prod["producer"]
    with pytest.raises(ValidationError) as info:
        Profile(**prod)
        assert "Must provide a producer" in str(info.value)


def test_invalid_consumer(confluent_consumer_profile: Profile) -> None:
    """a consumer without a consumer connector should fail"""
    prod = confluent_consumer_profile.dict()
    del prod["consumer"]
    with pytest.raises(ValidationError) as info:
        Profile(**prod)
        assert "Must provide a consumer" in str(info.value)


def test_invalid_handler_config(confluent_consumer_profile: Profile) -> None:
    """a data schema model without a handler should fail"""
    prod = confluent_consumer_profile.dict()
    del prod["model_handler"]
    with pytest.raises(ValidationError) as info:
        Profile(**prod)
    assert "Must provide both or none of model_handler|data_model" in str(info.value)
