from typing import TypeVar

from .models.pydantic_model import ComponentMessage, QueueMessage

ComponentMessageType = TypeVar("ComponentMessageType", bound=ComponentMessage)

__all__ = ["ComponentMessage", "QueueMessage", "ComponentMessageType"]
