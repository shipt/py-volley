from typing import Any, Dict

import pytest
from pydantic import ValidationError

from volley.config import get_configs
from volley.profiles import ConnectionType, Profile, construct_profiles


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
    """verify loading of named profiles"""
    for _, cfg in config_dict.items():
        # is added by Engine()
        cfg["connection_type"] = ConnectionType.CONSUMER
    profile = construct_profiles(config_dict)
    for _, p in profile.items():
        assert p.model_handler is not None
        assert p.data_model is not None


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
