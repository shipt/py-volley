from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from engine.data_models import BundleMessage


@dataclass  # type: ignore
class Consumer(ABC):
    """Base for a consumer (kafka or rsmq)"""

    host: str
    queue_name: str

    @abstractmethod
    def consume(
        self, queue_name: str, timeout: float = 30, poll_interval: float = 1
    ) -> BundleMessage:
        """consumes a message to any queue. decodes from queue's data type to BaseMessage schema"""

    @abstractmethod
    def delete_message(self, queue_name: str, message_id: Any = None) -> bool:
        """deletes a message from a queue"""

    @abstractmethod
    def on_fail(self) -> None:
        """perform some action when downstream operation fails"""
