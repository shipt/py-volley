# Copyright (c) Shipt.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from typing import Any, List, Tuple, Union

from prometheus_client import Counter

from volley.logging import logger
from volley.models.base import model_message_handler
from volley.queues import Queue

MESSAGES_PRODUCED = Counter(
    "messages_produced_count", "Messages produced to output destination(s)", ["volley_app", "source", "destination"]
)


def produce_handler(
    outputs: Union[List[Tuple[str, Any]], List[Tuple[str, Any, dict[str, Any]]]],
    queue_map: dict[str, Queue],
    app_name: str,
    input_name: str,
) -> List[bool]:
    """Handles producing messages to output queues

    Returns:
        List[bool]: A bool for success/fail of producing to each output target
    """
    all_produce_status: List[bool] = []
    for qname, component_msg, *args in outputs:
        try:
            out_queue = queue_map[qname]
        except KeyError as e:
            raise NameError(f"App not configured for output queue {e}")

        # prepare and validate output message
        if out_queue.data_model is not None and not isinstance(component_msg, out_queue.data_model):
            raise TypeError(f"{out_queue.name=} expected '{out_queue.data_model}' - object is '{type(component_msg)}'")

        try:
            # serialize message
            serialized = model_message_handler(
                data_model=component_msg,
                model_handler=out_queue.model_handler,
                serializer=out_queue.serializer,
            )
            if len(args):
                kwargs: dict[str, Any] = args[0]
            else:
                kwargs = {}
            status = out_queue.producer_con.produce(queue_name=out_queue.value, message=serialized, **kwargs)
            MESSAGES_PRODUCED.labels(volley_app=app_name, source=input_name, destination=qname).inc()
            if not status:
                logger.error("failed producing message to %s" % out_queue.name)
        except Exception:
            logger.exception("failed producing message to %s" % out_queue.name)
            status = False
        all_produce_status.append(status)
    return all_produce_status
