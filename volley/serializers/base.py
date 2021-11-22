from abc import ABC, abstractmethod
from typing import Any


class BaseSerialization(ABC):
    """Base class for serializing and deserializing queue data"""

    @abstractmethod
    def serialize(self, message: Any, *args: Any, **kwargs: Any) -> bytes:
        """serialize to queue"""

    @abstractmethod
    def deserialize(self, message: Any, *args: Any, **kwargs: Any) -> Any:
        """deserialize from queue"""
