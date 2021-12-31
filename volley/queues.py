# Copyright (c) Shipt.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, NamedTuple, Optional, Type

from pydantic import BaseModel, Field, root_validator, validator

from volley.config import GLOBALS, get_configs, import_module_from_string, load_yaml
from volley.connectors.base import Consumer, Producer
from volley.logging import logger
from volley.models import PydanticModelHandler
from volley.models.base import BaseModelHandler
from volley.profiles import ConnectionType, Profile, construct_profiles
from volley.serializers import OrJsonSerialization
from volley.serializers.base import BaseSerialization


class DLQNotConfiguredError(Exception):
    """raised when message processes fails and no DLQ configured"""

    pass


@dataclass
class Queue:
    """a Queue object represents everything we need to know about a queue"""

    # alias for the queue
    name: str
    # system name for the queue. for example, some really long kafka topic name
    value: str
    profile: Profile

    # instantiated post-init
    data_model: Optional[Any] = field(init=False, default=None)
    model_handler: Optional[BaseModelHandler] = field(init=False, default=None)
    serializer: Optional[BaseSerialization] = field(init=False, default=None)

    # initialized queue connections
    # these are initialized by calling connect()
    # consumer_con: Consumer
    # producer_con: Producer

    # optional configurations to pass through to connectors
    pass_through_config: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Load modules provided in Profile"""
        # data model is assigned by not instantiated
        if self.profile.data_model is not None:
            self.data_model = import_module_from_string(self.profile.data_model)

        # model_handler and serializer are instantiated on init
        if self.profile.model_handler is not None:
            self.model_handler = import_module_from_string(self.profile.model_handler)()
        if self.profile.serializer is not None:
            self.serializer = import_module_from_string(self.profile.serializer)()

        if not isinstance(self.pass_through_config, dict):
            raise TypeError(f"Connector config for `{self.name}` must be of type `dict`")

    def connect(self, con_type: ConnectionType) -> None:
        """instantiate the connector class"""
        if con_type == ConnectionType.CONSUMER:
            if self.profile.consumer is None:
                raise ValueError("Must provide a consumer connector")
            _class = import_module_from_string(self.profile.consumer)
            self.consumer_con = _class(queue_name=self.value, config=self.pass_through_config.copy())
        elif con_type == ConnectionType.PRODUCER:
            if self.profile.producer is None:
                raise ValueError("Must provide a producer connector")
            _class = import_module_from_string(self.profile.producer)
            self.producer_con = _class(queue_name=self.value, config=self.pass_through_config.copy())
        else:
            raise TypeError(f"{con_type=} is not valid")


def construct_queue_map(profiles: Dict[str, Profile], configs: dict[str, dict[str, str]]) -> Dict[str, Queue]:
    """Constructs a mapping of queue_name: Queue for each requested queue"""

    queue_map: Dict[str, Queue] = {}
    for qname, profile in profiles.items():
        q_config = configs[qname]
        cfg: Any = q_config.get("config", {})
        queue = Queue(
            name=qname,
            value=q_config["value"],
            profile=profile,
            pass_through_config=cfg,
        )
        queue_map[qname] = queue

    return queue_map
