from typing import Any, Protocol


class BaseSerialization(Protocol):
    def serialize(self, message: dict[str, Any]) -> bytes:
        ...

    def deserialize(self, message: bytes) -> dict[str, Any]:
        ...
