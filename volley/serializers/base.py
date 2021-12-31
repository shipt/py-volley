# Copyright (c) Shipt.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from abc import ABC, abstractmethod
from typing import Any


class BaseSerialization(ABC):
    """Base class for serializing and deserializing queue data"""

    @abstractmethod
    def serialize(self, message: dict[Any, Any]) -> bytes:
        """serialize to queue"""

    @abstractmethod
    def deserialize(self, message: bytes) -> Any:
        """deserialize from queue"""


class NullSerializer(BaseSerialization):
    """used if a consumer/producer needs to bypass serialization

    for example - if a component outputs an object of type MyComponentClass and
        its custom plugin must accept an object the same type. Serialization is effectively handled
        directly in the connector.
    """

    def serialize(self, message: Any) -> Any:
        """returns the message"""
        return message

    def deserialize(self, message: Any) -> Any:
        """returns the message"""
        return message
