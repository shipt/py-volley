from typing import Dict

import pytest
from pydantic.main import BaseModel

from volley.config import load_yaml
from volley.data_models import QueueMessage
from volley.queues import (
    Queue,
    available_queues,
    import_module_from_string,
    interpolate_kafka_topics,
)


def test_load_yaml_success() -> None:
    d = load_yaml("./example/volley_config.yml")
    assert "queues" in d
    assert isinstance(d, dict)


def test_load_yaml_fail() -> None:
    with pytest.raises(FileNotFoundError):
        load_yaml("donotexist")


def test_available_queues() -> None:
    all_queues: Dict[str, Queue] = available_queues("./example/volley_config.yml")

    for qname, q in all_queues.items():
        assert isinstance(qname, str)
        assert isinstance(q, Queue)


# def test_queues_from_yaml() -> None:
#     queue_list = ["input-queue", "dead-letter-queue"]
#     queues = queues_from_yaml(queue_list, yaml_path="./example/volley_config.yml")
#     for qname, queue in queues.items():
#         assert isinstance(queue, Queue)
#         assert qname == queue.name
#         if queue.type == "kafka":
#             assert "{{ env  }}" not in queue.value


# def test_queues_from_dict(config_dict: dict[str, dict[str, str]]) -> None:
#     queues: dict[str, Queue] = queues_from_dict(config_dict)
#     for qname, queue in queues.items():
#         assert isinstance(queue, Queue)
#         assert qname == queue.name

#         expected_vals: dict[str, str] = config_dict[queue.name]

#         # make sure none the config values were overrided
#         for k, v in expected_vals.items():
#             assert getattr(queue, k) == v


def test_import_module_from_string() -> None:
    class_module = import_module_from_string("volley.data_models.QueueMessage")

    instance = class_module(message_id="abc", message={"data": "message"})

    assert issubclass(class_module, BaseModel)
    assert isinstance(instance, QueueMessage)


def test_interpolate_kafka_topics() -> None:
    templated = "{{ env }}.kafka.input"
    cfg = {"type": "kafka", "value": templated}
    interpolated = interpolate_kafka_topics(cfg)

    assert interpolated["value"] == "localhost.kafka.input"
