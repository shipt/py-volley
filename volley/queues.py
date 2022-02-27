# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from volley.config import import_module_from_string
from volley.models.base import BaseModelHandler
from volley.profiles import ConnectionType, Profile
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
    pass_through_config: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Load modules provided in Profile"""
        # data model is assigned by not instantiated
        if isinstance(self.profile.data_model, str):
            self.data_model = import_module_from_string(self.profile.data_model)
        elif self.profile.data_model is not None:
            self.data_model = self.profile.data_model

        # model_handler and serializer are instantiated on init
        if isinstance(self.profile.model_handler, str):
            self.model_handler = import_module_from_string(self.profile.model_handler)()
        elif self.profile.model_handler is not None:
            self.model_handler = self.profile.model_handler()
        if isinstance(self.profile.serializer, str):
            self.serializer = import_module_from_string(self.profile.serializer)()
        elif self.profile.serializer is not None:
            self.serializer = self.profile.serializer()

    def connect(self, con_type: ConnectionType) -> None:
        """instantiate the connector class"""
        if con_type == ConnectionType.CONSUMER:
            if self.profile.consumer is None:
                raise ValueError("Must provide a consumer connector")
            if isinstance(self.profile.consumer, str):
                _class = import_module_from_string(self.profile.consumer)
            else:
                _class = self.profile.consumer
            self.consumer_con = _class(queue_name=self.value, config=self.pass_through_config.copy())
        elif con_type == ConnectionType.PRODUCER:
            if self.profile.producer is None:
                raise ValueError("Must provide a producer connector")
            if isinstance(self.profile.producer, str):
                _class = import_module_from_string(self.profile.producer)
            else:
                _class = self.profile.producer
            self.producer_con = _class(queue_name=self.value, config=self.pass_through_config.copy())
        else:
            raise TypeError(f"{con_type=} is not valid")


def construct_queue_map(profiles: Dict[str, Profile], configs: Dict[str, Dict[str, str]]) -> Dict[str, Queue]:
    """Constructs a mapping of queue_name: Queue for each requested queue"""

    queue_map: Dict[str, Queue] = {}
    for qname, profile in profiles.items():
        q_config = configs[qname]
        cfg: Any = q_config.get("config", {})
        if (value := q_config.get("value")) is None:
            raise KeyError(f"Must provide `value` in configuration for `{qname}`")
        queue = Queue(
            name=qname,
            value=value,
            profile=profile,
            pass_through_config=cfg,
        )
        queue_map[qname] = queue

    return queue_map
