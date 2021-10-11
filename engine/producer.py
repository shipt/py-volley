from abc import ABC, abstractmethod
from dataclasses import dataclass

from engine.data_models import BundleMessage


@dataclass  # type: ignore
class Producer(ABC):
    """Basic protocol for a producer (kafka or rsmq)"""
    host: str
    queue_name: str

    @abstractmethod
    def produce(self, queue_name: str, message: BundleMessage) -> None:
        """publishes a message to any queue"""
