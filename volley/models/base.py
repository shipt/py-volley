from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple

from volley.logging import logger
from volley.serializers.base import BaseSerialization


class BaseModelHandler(ABC):
    """base definition for a schema validator

    Provides the method for constructing an object with a schema
    """

    @abstractmethod
    def construct(self, message: Any, schema: Any) -> Any:
        """turns a raw message into a data model"""

    @abstractmethod
    def deconstruct(self, model: Any) -> Any:
        """turns data model into a raw type"""


def message_model_handler(
    message: Any,
    schema: Any,
    model_handler: BaseModelHandler,
    serializer: Optional[BaseSerialization] = None,
) -> Tuple[Any, bool]:
    """handles converting data from connector to data model for application

    Args:
        message (Any): [description]
        schema (Any): [description]
        model_handler (Optional[BaseModelHandler], optional): [description]. Defaults to None.
        serializer (Optional[BaseSerialization], optional): [description]. Defaults to None.

    Returns:
        Tuple[Any, bool]: (data_model, True) on success, or (raw_message, False)
    """
    # input serialization
    # optional - some frameworks may handle model constuction and serialization in one-shot
    deserialized_msg: Any
    if serializer is not None:
        try:
            deserialized_msg = serializer.deserialize(message)
        except Exception:
            logger.exception(f"Deserialization failed {message=} - {serializer=}")
            raise
    else:
        # serializer is disabled
        deserialized_msg = message

    # model construction
    # schema validation can only happen if deserialization succeeds
    try:
        data_model = model_handler.construct(
            message=deserialized_msg,
            schema=schema,
        )
        return (data_model, True)
    except Exception:
        logger.exception(f"Failed model construction. message={deserialized_msg}. schema={schema}")
        return (deserialized_msg, False)


def model_message_handler(
    data_model: Any,
    model_handler: BaseModelHandler,
    serializer: Optional[BaseSerialization] = None,
) -> Any:
    """converts a data model to data ready for a connector"""

    try:
        # one block - if any of this fails, we crash hard because
        # we dont want to try to recover if we cant publish

        # convert data model to raw type
        raw = model_handler.deconstruct(data_model)

        if serializer is not None:
            # serialize if asked
            return serializer.serialize(raw)
        else:
            return raw
    except Exception:
        logger.exception(f"failed transporting message to connector: {data_model}")
        raise
