# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from typing import TypeVar

from volley.models.pydantic_model import GenericMessage, QueueMessage

GenericMessageType = TypeVar("GenericMessageType", bound=GenericMessage)

__all__ = ["GenericMessage", "QueueMessage", "GenericMessageType"]
