from typing import Any, Dict, List, Optional
from uuid import uuid4

import pytest
from pydantic import ValidationError

from volley import Engine, QueueConfig
from volley.config import get_configs, import_module_from_string
from volley.profiles import ConnectionType, Profile, construct_profiles


def test_non_exist_profile() -> None:
    """requesting a non existent profile should fail"""
    non_exist_profile = f"non_exist_{str(uuid4())}"
    invalid = {"rando_queue": {"profile": non_exist_profile, "connection_type": ConnectionType.PRODUCER}}
    with pytest.raises(ValueError) as err:
        construct_profiles(invalid)

    assert non_exist_profile in str(err.value)


def test_non_exist_profile_init(config_dict: Dict[str, Dict[str, Any]]) -> None:
    """requesting a non existent profile should fail on init too"""
    non_exist_profile = f"non_exist_{str(uuid4())}"
    config_dict["input-topic"]["profile"] = non_exist_profile

    with pytest.raises(ValueError) as err:
        Engine(input_queue="input-topic", metrics_port=None, queue_config=config_dict)

    assert non_exist_profile in str(err.value)


def test_construct_producer_profiles() -> None:
    """verify all supported configurations are valid producer"""
    all_profiles = get_configs()["profiles"]
    for _, p_config in all_profiles.items():
        p_config["connection_type"] = ConnectionType.PRODUCER
    profile_map: Dict[str, Profile] = construct_profiles(all_profiles)

    for p, profile in profile_map.items():
        assert isinstance(p, str)
        assert p in all_profiles
        assert isinstance(profile, Profile)


def test_construct_consumer_profiles() -> None:
    """verify all supported configurations are valid consumers"""
    all_profiles = get_configs()["profiles"]
    for _, p_config in all_profiles.items():
        p_config["connection_type"] = ConnectionType.CONSUMER
    profile_map: Dict[str, Profile] = construct_profiles(all_profiles)

    for p, profile in profile_map.items():
        assert isinstance(p, str)
        assert p in all_profiles
        assert isinstance(profile, Profile)


def test_load_named_profiles(config_dict: Dict[str, Dict[str, Any]]) -> None:
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
    prod = confluent_producer_profile.model_dump()
    del prod["producer"]
    with pytest.raises(ValidationError) as info:
        Profile(**prod)
    assert "Must provide a producer" in str(info.value)


def test_invalid_consumer(confluent_consumer_profile: Profile) -> None:
    """a consumer without a consumer connector should fail"""
    prod = confluent_consumer_profile.model_dump()
    del prod["consumer"]
    with pytest.raises(ValidationError) as info:
        Profile(**prod)
    assert "Must provide a consumer" in str(info.value)


def test_invalid_handler_config(confluent_consumer_profile: Profile) -> None:
    """a data schema model without a handler should fail"""
    prod = confluent_consumer_profile.model_dump()
    del prod["model_handler"]
    with pytest.raises(ValidationError) as info:
        Profile(**prod)
    assert "Must provide both or none of model_handler|data_model" in str(info.value)


@pytest.mark.parametrize(
    "data_model,model_handler,serializer",
    [
        (None, None, None),
        ("volley.data_models.GenericMessage", "volley.models.PydanticParserModelHandler", None),
        (
            "volley.data_models.GenericMessage",
            "volley.models.PydanticModelHandler",
            "volley.serializers.msgpack_serializer.MsgPackSerialization",
        ),
    ],
)
def test_profile_override(data_model: Optional[str], model_handler: Optional[str], serializer: Optional[str]) -> None:
    """all or none of a profiles can be overridden by the user"""
    qname = "test-topic"
    consumer_group = str(uuid4())
    qvalue = "test.topic"

    confluent = "confluent"
    confluent_profile_data = get_configs()["profiles"][confluent]

    cfg: Dict[str, Any] = {
        qname: {
            "value": qvalue,
            "profile": confluent,
            "model_handler": model_handler,
            "data_model": data_model,
            "serializer": serializer,
            "config": {"group.id": consumer_group},
        }
    }
    cfg_obj: List[QueueConfig] = [QueueConfig(name=qname, **cfg[qname])]

    # run tests against both the dict and QueueConfig object
    for _cfg in [cfg, cfg_obj]:
        app = Engine(input_queue=qname, queue_config=_cfg, metrics_port=None)  # type: ignore
        test_topic_queue = app.queue_map[qname]

        if data_model is None:
            assert test_topic_queue.data_model is data_model
        else:
            # data_model is not the class object, not the instance
            # model_handler creates the instance of data_model
            assert test_topic_queue.data_model == import_module_from_string(data_model)

        if model_handler is None:
            assert test_topic_queue.model_handler is model_handler
        else:
            assert isinstance(test_topic_queue.model_handler, import_module_from_string(model_handler))

        if serializer is None:
            assert test_topic_queue.serializer is serializer
        else:
            assert isinstance(test_topic_queue.serializer, import_module_from_string(serializer))

        # these Queue attributes are str
        assert test_topic_queue.name == qname
        assert test_topic_queue.value == qvalue

        # profile attributes are Optional[str]
        assert test_topic_queue.profile.model_handler is model_handler
        assert test_topic_queue.profile.data_model is data_model

        # verify not overriden
        assert test_topic_queue.profile.producer == confluent_profile_data["producer"]
        assert test_topic_queue.profile.consumer == confluent_profile_data["consumer"]
