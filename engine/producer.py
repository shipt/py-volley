from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.logging import logger
from engine.data_models import QueueMessage


@dataclass  # type: ignore
class Producer(ABC):
    """Basic protocol for a producer (kafka or rsmq)"""

    host: str
    queue_name: str

    @abstractmethod
    def produce(self, queue_name: str, message: QueueMessage) -> bool:
        """publishes a message to any queue"""
        logger.info(f"producing to: {queue_name=}")
        return True

    def shutdown(self) -> None:
        """perform some action when shutting down the application"""
