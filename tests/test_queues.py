import pytest

from volley.profiles import Profile
from volley.queues import Queue, construct_queue_map


def test_bad_config_type(confluent_consumer_profile: Profile) -> None:
    """config passed through to connector must be a dictionary"""
    with pytest.raises(TypeError):
        Queue(
            name="test",
            value="long_value",
            profile=confluent_consumer_profile,
            pass_through_config="bad_value",  # type: ignore
        )


def test_bad_connnect_type(confluent_consumer_profile: Profile) -> None:
    """config passed through to connector must be a dictionary"""
    q = Queue(
        name="test",
        value="long_value",
        profile=confluent_consumer_profile,
    )
    with pytest.raises(TypeError):
        q.connect("BAD_TYPE")  # type: ignore


def test_missing_queue_attr(confluent_consumer_profile: Profile, config_dict: dict[str, dict[str, str]]) -> None:
    del config_dict["input-topic"]["value"]
    pm = {"input-topic": confluent_consumer_profile}

    with pytest.raises(KeyError):
        construct_queue_map(profiles=pm, configs=config_dict)
