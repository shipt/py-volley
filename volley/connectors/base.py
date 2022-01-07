# Copyright (c) Shipt.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from volley.data_models import QueueMessage


@dataclass  # type: ignore
class BaseConsumer(ABC):
    """Base for a consumer (kafka, rsmq)"""

    queue_name: str
    host: Optional[str] = None
    config: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def consume(self, queue_name: str) -> Optional[QueueMessage]:
        """consumes a message to any queue. return None when there are no messages to consume"""

    @abstractmethod
    def delete_message(self, queue_name: str, message_context: Any) -> bool:
        """deletes a message from a queue"""

    @abstractmethod
    def on_fail(self) -> None:
        """perform some action when downstream operation fails"""

    def shutdown(self) -> None:
        """perform some action when shutting down the application"""


@dataclass  # type: ignore
class BaseProducer(ABC):
    """Basic protocol for a producer (kafka or rsmq)"""

    queue_name: str
    host: Optional[str] = None
    config: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def produce(self, queue_name: str, message: Any, **kwargs: Any) -> bool:
        """publishes a message to any queue"""

    def shutdown(self) -> None:
        """perform some action when shutting down the application"""
