# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from volley.data_models import QueueMessage


@dataclass  # type: ignore
class BaseConsumer(ABC):
    """Base class for implementing a consumer"""

    queue_name: str
    host: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def consume(self) -> Optional[QueueMessage]:
        """consumes a message from any queue.
        Returns a QueueMessage object on success, or None when there are no messages
        """

    @abstractmethod
    def on_success(self, message_context: Any) -> None:
        """action to take when a message has been successfully consumed.
        For example, delete the message that was consumed.
        """

    @abstractmethod
    def on_fail(self, message_context: Any) -> None:
        """action to perform when serialization, or data validation has failed"""

    @abstractmethod
    def shutdown(self) -> None:
        """perform some action when shutting down the application.
        For example, close a connection or leave a consumer group
        """


@dataclass  # type: ignore
class BaseProducer(ABC):
    """Base class for implementing a producer"""

    queue_name: str
    host: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    callback_delivery: bool = False
    on_success: Optional[Callable[[Any], None]] = None
    on_fail: Optional[Callable[[Any], None]] = None

    @abstractmethod
    def produce(self, queue_name: str, message: Any, message_context: Optional[Any], **kwargs: Any) -> bool:
        """Publish a message to a queue

        Args:
            queue_name (str): Destination queue name.
            message (Any): The message to publish.
            message_context (Any): Context for the consumed message.
                Often a message id, or a Kafka Message object.
                Used for Producer callbacks to consumer.

        Returns:
            bool: status of the produce operation
        """

    @abstractmethod
    def shutdown(self) -> None:
        """perform some action when shutting down the application"""
