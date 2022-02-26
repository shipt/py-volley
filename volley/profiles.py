# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from copy import deepcopy
from enum import Enum, auto
from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel, root_validator, validator

from volley.config import get_configs
from volley.connectors.base import BaseConsumer, BaseProducer
from volley.logging import logger
from volley.models.base import BaseModelHandler
from volley.serializers.base import BaseSerialization


class ConnectionType(Enum):
    """types of connections to queues"""

    PRODUCER: auto = auto()
    CONSUMER: auto = auto()


class Profile(BaseModel):

    connection_type: ConnectionType
    # dot path to the object, or the object itself
    consumer: Optional[Union[str, Type[BaseConsumer]]]
    producer: Optional[Union[str, Type[BaseProducer]]]
    model_handler: Optional[Union[str, Type[BaseModelHandler]]]
    data_model: Optional[Union[str, type]]
    serializer: Optional[Union[str, Type[BaseSerialization]]]

    @validator("model_handler", "data_model", "serializer")
    @classmethod
    def validate_nullable(cls, value: Optional[str]) -> Optional[str]:
        """Ensures str or None types parse as `None`
        This needs to be the top (first) validator
        """
        if str(value).lower() not in ["none", "disabled"]:
            return value
        else:
            return None

    @root_validator
    @classmethod
    def validate_connectors(cls, values: Dict[str, Any]) -> Any:
        if values.get("producer") is None and values["connection_type"] == ConnectionType.PRODUCER:
            raise ValueError("Invalid Profile. Must provide a producer for output queues.")
        if values.get("consumer") is None and values["connection_type"] == ConnectionType.CONSUMER:
            raise ValueError("Invalid Profile. Must provide a consumer for input queues.")
        return values

    @root_validator
    @classmethod
    def validate_handler(cls, values: Dict[str, Any]) -> Any:
        """Volley cannot construct data into a data model without a model handler
        both model_handler and data_model can be None, however
        """
        data_model = values.get("data_model")
        model_handler = values.get("model_handler")
        if data_model is not None and model_handler is not None:
            # happy path - both are provided
            return values
        elif data_model is None and model_handler is None:
            # happy, but unconventional path
            # could happen if someone wants to send bytes to their application
            logger.info("model_handler and data_model are disabled")
            return values
        else:
            raise ValueError(
                "Invalid Profile. Must provide both or none of model_handler|data_model"
                f"{data_model=} -- {model_handler=}"
            )


def construct_profiles(queue_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Profile]:
    """Constructs a profile from each queue configuration provided by user
    User behavior:
        1. Specifies a named profile with no overrides
        2. Specifies a named profile and provide overrides
        3. Does not specify a profile and provides all values
    """
    supported_profiles: Dict[str, Dict[str, str]] = get_configs()["profiles"]

    constructed_profiles: Dict[str, Profile] = {}

    for q_name, q_cfg in queue_configs.items():
        profile_requested = q_cfg.get("profile")
        if profile_requested in supported_profiles:
            this_profile: Dict[str, str] = deepcopy(supported_profiles[profile_requested])
            # override the requested profile with any user provided cfgs
            this_profile.update(q_cfg)
        elif profile_requested is None:
            # user can provide all required configs
            # and is validated in Profile()
            this_profile = deepcopy(q_cfg)
        else:
            raise ValueError(
                f"`{profile_requested}` is not a valid profile name. "
                f"Available profiles: `{list(supported_profiles.keys())}`"
            )
        constructed_profiles[q_name] = Profile(**this_profile)

    return constructed_profiles
