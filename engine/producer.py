from abc import ABC, abstractmethod
from dataclasses import dataclass

from engine.data_models import BundleMessage

from core.logging import logger

@dataclass  # type: ignore
class Producer(ABC):
    """Basic protocol for a producer (kafka or rsmq)"""
    host: str
    queue_name: str

    @abstractmethod
    def produce(self, queue_name: str, message: BundleMessage) -> bool:
        """publishes a message to any queue"""
        logger.info(f"producing to: {queue_name=}")
        return True