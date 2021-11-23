from abc import ABC, abstractmethod
from typing import Any, Tuple

from volley.logging import logger

class BaseSerialization(ABC):
    """Base class for serializing and deserializing queue data"""

    @abstractmethod
    def serialize(self, message: Any, *args: Any, **kwargs: Any) -> bytes:
        """serialize to queue"""

    @abstractmethod
    def deserialize(self, message: Any, *args: Any, **kwargs: Any) -> Any:
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


def handle_serializer(serializer: BaseSerialization, message: Any, operation: str, *args: Any, **kwargs: Any) -> Tuple[Any, bool]:
    """handles errors in serializer opertions (serialize|deserialize)

    Args:
        serializer (BaseSerialization): the provided serilization plugin
        message (Any): message to serialize|deserialize
        operation (str): enum of serialize|deserialize

    Returns:
        Tuple[Any, bool]: returns the processed message and a success/fail status.
            on fail, the message will be the same original, unprocessed message 
    """
    if operation not in ("serialize", "deserialize"):
        raise NotImplementedError(f"{operation} not a valid serilizer method")
    
    op = getattr(serializer, operation)
    try:
        success_msg = op(message, *args, **kwargs)
        return (success_msg, True)
    except Exception:
        logger.exception(f"Failed {operation} on {message=}")
        return (message, False)
