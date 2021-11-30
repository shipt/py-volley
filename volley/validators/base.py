from abc import ABC, abstractmethod
from typing import Any, Tuple

from volley.logging import logger


class BaseValidation(ABC):
    """base definition for a schema validator

    Provides the method for constructing an object with a schema
    """

    @abstractmethod
    def construct(self, message: Any, schema: Any) -> Any:
        """Converts serialized message to a schema object"""


def handle_validator(validator: BaseValidation, schema: Any, message: Any) -> Tuple[Any, bool]:
    """Handles converting serialized message to an object

    Args:
        validator (BaseValidation): The provided validator class
        schema (Any): the schema to which the message should adhere
        message (Any): Message that needs validation

    Returns:
        Tuple[Any, bool]: Returns the object, and its success status
            Returns the raw message on failure.
    """
    try:
        validated = validator.construct(message=message, schema=schema)
        return (validated, True)
    except Exception:
        logger.exception(f"{validator=} validation failed on {message}")
        return (message, False)
