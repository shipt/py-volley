from abc import ABC, abstractmethod
from dataclasses import dataclass

from engine.data_models import BundleMessage


@dataclass  # type: ignore
class Consumer(ABC):
    """Base for a consumer (kafka or rsmq)"""
    host: str
    queue_name: str

    @abstractmethod
    def consume(self, queue_name: str, timeout: float, poll_interval: float) -> BundleMessage:
        """consumes a message to any queue"""

    @abstractmethod
    def delete_message(self, queue_name: str, message_id: str=None) -> bool:
        """deletes a message from a queue"""
