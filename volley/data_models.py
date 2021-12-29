# Copyright (c) Shipt.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from typing import TypeVar

from volley.models.pydantic_model import ComponentMessage, QueueMessage

ComponentMessageType = TypeVar("ComponentMessageType", bound=ComponentMessage)

__all__ = ["ComponentMessage", "QueueMessage", "ComponentMessageType"]
