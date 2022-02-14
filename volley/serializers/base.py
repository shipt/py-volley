# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSerialization(ABC):
    """Base class for serializing and deserializing queue data"""

    @abstractmethod
    def serialize(self, message: Dict[Any, Any]) -> bytes:
        """serialize to queue"""

    @abstractmethod
    def deserialize(self, message: bytes) -> Any:
        """deserialize from queue"""
