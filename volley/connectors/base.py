from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from volley.data_models import QueueMessage
from volley.logging import logger


@dataclass  # type: ignore
class Consumer(ABC):
    """Base for a consumer (kafka, rsmq)"""

    queue_name: str
    host: Optional[str] = None

    @abstractmethod
    def consume(self, queue_name: str, timeout: float = 30, poll_interval: float = 1) -> Optional[QueueMessage]:
        """consumes a message to any queue. return None when there are no messages to consume"""

    @abstractmethod
    def delete_message(self, queue_name: str, message_id: Any = None) -> bool:
        """deletes a message from a queue"""

    @abstractmethod
    def on_fail(self) -> None:
        """perform some action when downstream operation fails"""

    def shutdown(self) -> None:
        """perform some action when shutting down the application"""


@dataclass  # type: ignore
class Producer(ABC):
    """Basic protocol for a producer (kafka or rsmq)"""

    queue_name: str
    host: Optional[str] = None

    @abstractmethod
    def produce(self, queue_name: str, message: QueueMessage) -> bool:
        """publishes a message to any queue"""

    def shutdown(self) -> None:
        """perform some action when shutting down the application"""
