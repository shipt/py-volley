from abc import ABC, abstractmethod
from dataclasses import dataclass

from components.data_models import QueueMessage
from core.logging import logger


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
