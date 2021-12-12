from typing import Any, List, NamedTuple, Optional, Tuple, Union

from pydantic import BaseModel


class SendMessage(NamedTuple):
    """transport object between connector and engine

    message_context: any object. used to pass data or configuration between
        consumption actions; consume, delete, on_fail, shutdown.
        for example - database connection, Kafka message context, etc.
    message: raw message from connector
    connector_kwargs: any runtime configuration for a connector's
        produce method
    """

    destination: str
    message: Optional[Any]
    connector_kwargs: dict[str, Any]
