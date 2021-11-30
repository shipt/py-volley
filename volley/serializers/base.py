from abc import ABC, abstractmethod
from typing import Any


class BaseSerialization(ABC):
    """Base class for serializing and deserializing queue data"""

    @abstractmethod
    def serialize(self, message: dict[Any, Any], *args: Any, **kwargs: Any) -> bytes:
        """serialize to queue"""

    @abstractmethod
    def deserialize(self, message: bytes, *args: Any, **kwargs: Any) -> Any:
        """deserialize from queue"""


class NullSerializer(BaseSerialization):
    """used if a consumer/producer needs to bypass serialization

    for example - if a component outputs an object of type MyComponentClass and
        its custom plugin must accept an object the same type. Serialization is effectively handled
        directly in the connector.
    """

    def serialize(self, message: Any, *args: Any, **kwargs: Any) -> Any:
        """returns the message"""
        return message

    def deserialize(self, message: Any, *args: Any, **kwargs: Any) -> Any:
        """returns the message"""
        return message
