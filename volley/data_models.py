from typing import TypeVar

from volley.validators.pydantic_validator import ComponentMessage, QueueMessage

ComponentMessageType = TypeVar("ComponentMessageType", bound=ComponentMessage)

__all__ = ["ComponentMessage", "QueueMessage", "ComponentMessageType"]
