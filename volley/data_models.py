from typing import Any, Tuple, TypeVar

from pydantic import BaseModel, Extra

from volley.logging import logger


class ComponentMessage(BaseModel):
    """base class for all inputs/outputs from a componet"""

    class Config:
        extra = Extra.allow


class QueueMessage(BaseModel):
    """message in its raw state off a queue
    message_id: any identifier for a message on a queue.
        used for deleting or markng a message as success after post-processing
    """

    message_id: Any
    message: Any


ComponentMessageType = TypeVar("ComponentMessageType", bound=ComponentMessage)


def schema_handler(schema: type, message: Any) -> Tuple[ComponentMessageType, bool]:
    """handles errors related to schema validation

    Args:
        schema (type): the provided schema object
        message (Any): [description]

    Returns:
        BaseModel: [description]
    """
    # TODO: We need a new base class for schemas. To be more flexible,
    # schemas should provide a .construct or .validate method. The default
    # for Pydantic can be a simple .from_obj or (**message)
    try:
        validated = schema(**message)
        return (validated, True)
    except Exception:
        logger.exception(f"{schema=} validation failed on {message}")
        return (message, False)
