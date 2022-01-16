# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from abc import ABC, abstractmethod
from time import time
from typing import Any, Optional, Tuple

from prometheus_client import Summary

from volley.logging import logger
from volley.serializers.base import BaseSerialization

PROCESS_TIME = Summary("data_model_process_seconds", "Time handling message to data model (seconds)", ["process"])


class BaseModelHandler(ABC):
    """Base definition for a schema validator

    Provides the method for constructing an object with a schema
    """

    @abstractmethod
    def construct(self, message: Any, schema: Any) -> Any:
        """turns a raw message into a data model

        The purpose is to provide the definitions on how to turn a
        message from a serializer into a message that an application
        is ready to consume. If the serializer will return a dict, then
        the type of the param `message` would be `dict`. The construct
        method would parse the `dict` into whatever data model that the
        application is expecting to received.

        Args:
            message (Any): A message to construct into a data model specified by `schema`.
                The message can be of any type so long as  .construct() and .deconstruct()
                have implementation details to handle the type.
            schema (Any): The data model definition. `message` is used to create an instance
                of `schema`

        Returns:
            Any: an instance of class `schema`
        """

    @abstractmethod
    def deconstruct(self, model: Any) -> Any:
        """turns data model into a raw type"""


def message_model_handler(
    message: Any,
    schema: Any,
    model_handler: Optional[BaseModelHandler] = None,
    serializer: Optional[BaseSerialization] = None,
) -> Tuple[Any, bool]:
    """handles converting data from connector to data model for application

    Args:
        message (Any): [description]
        schema (Any): [description]
        model_handler (Optional[BaseModelHandler], optional): [description]. Defaults to None.
        serializer (Optional[BaseSerialization], optional): [description]. Defaults to None.

    Returns:
        Tuple[Any, bool]: (data_model, True) on success, or (message, False)

    Raises:
        Exception: surfaced serializer or model handler
    """
    # input serialization
    # optional - some frameworks may handle model constuction and serialization in one-shot
    deserialized_msg: Any
    if serializer is not None:
        try:
            start = time()
            deserialized_msg = serializer.deserialize(message)
            duration = time() - start
            PROCESS_TIME.labels("deserialize").observe(duration)

        except Exception:
            logger.exception("Deserialization failed message=%s - serializer=%s", message, serializer)
            return (message, False)
    else:
        # serializer is disabled
        deserialized_msg = message

    # model construction
    if model_handler is not None:
        try:
            start = time()
            data_model = model_handler.construct(
                message=deserialized_msg,
                schema=schema,
            )
            duration = time() - start
            PROCESS_TIME.labels("construct").observe(duration)
            return (data_model, True)
        except Exception:
            logger.exception("Failed model construction. message=%s - schema=%s", deserialized_msg, schema)
            return (message, False)
    else:
        return (deserialized_msg, True)


def model_message_handler(
    data_model: Any,
    model_handler: Optional[BaseModelHandler] = None,
    serializer: Optional[BaseSerialization] = None,
) -> Any:
    """handles the convertion of a data model to data ready for a connector
    Most commonly this is a Pydantic model to bytes
    """

    try:
        # one block - if any of this fails, we crash hard because
        # we dont want to try to recover if we cant publish

        # convert data model to raw type
        start = time()
        if model_handler is not None:
            raw = model_handler.deconstruct(data_model)
        else:
            raw = data_model
        duration = time() - start
        PROCESS_TIME.labels("deconstruct").observe(duration)

        if serializer is not None:
            start = time()
            # serialize if asked
            serialized = serializer.serialize(raw)
            duration = time() - start
            PROCESS_TIME.labels("serialize").observe(duration)
            return serialized
        else:
            return raw
    except Exception:
        logger.exception("failed transporting message to connector: data_model=%s", data_model)
        raise
