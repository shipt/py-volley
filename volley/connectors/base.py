# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from volley.data_models import QueueMessage


@dataclass  # type: ignore
class BaseConsumer(ABC):
    """Base class for implementing a consumer"""

    queue_name: str
    host: Optional[str] = None
    config: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def consume(self, queue_name: str) -> Optional[QueueMessage]:
        """consumes a message from any queue.
        Returns a QueueMessage object on success, or None when there are no messages
        """

    @abstractmethod
    def on_success(self, queue_name: str, message_context: Any) -> bool:
        """action to take when a message has been successfully consumed.
        For example, delete the message that was consumed
        """

    @abstractmethod
    def on_fail(self) -> None:
        """action to perform when serializaion, or data validation has failed"""

    def shutdown(self) -> None:
        """perform some action when shutting down the application.
        For example, close a connection or leave a consumer group
        """


@dataclass  # type: ignore
class BaseProducer(ABC):
    """Base class for implementing a producer"""

    queue_name: str
    host: Optional[str] = None
    config: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def produce(self, queue_name: str, message: Any, **kwargs: Any) -> bool:
        """publish a message to a queue"""

    def shutdown(self) -> None:
        """perform some action when shutting down the application"""
