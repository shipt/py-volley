# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from prometheus_client import Counter

from volley.logging import logger
from volley.models.base import model_message_handler
from volley.queues import Queue

MESSAGES_PRODUCED = Counter(
    "messages_produced_count", "Messages produced to output destination(s)", ["volley_app", "source", "destination"]
)


@dataclass
class DeliveryReport:
    destination: Optional[str] = None
    asynchronous: bool = False
    status: bool = False


def produce_handler(
    outputs: Union[List[Tuple[str, Any]], List[Tuple[str, Any, Dict[str, Any]]]],
    queue_map: Dict[str, Queue],
    app_name: str,
    input_name: str,
    message_context: Any,
) -> List[DeliveryReport]:
    """Handles producing messages to output queues

        outputs: List of tuples returned by the Volley app function.
            (queue_name, message_object, optional_runtime_kwargs_for_producer)
        queue_map: mapping of queue_name:Queue object
        app_name: name provided by the application
        input_queue: becomes label in metric counter

    Returns:
        List[DeliveryReport]: DeliveryReport for each destination
    """
    all_delivery_reports: List[DeliveryReport] = []

    for qname, component_msg, *args in outputs:
        try:
            out_queue = queue_map[qname]
        except KeyError as e:
            raise KeyError(f"App not configured for output queue {e}")

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
                kwargs: Dict[str, Any] = args[0]
            else:
                kwargs = {}
            status = out_queue.producer_con.produce(
                queue_name=out_queue.value, message=serialized, message_context=message_context, **kwargs
            )
            MESSAGES_PRODUCED.labels(volley_app=app_name, source=input_name, destination=qname).inc()
            if not status:
                logger.error("failed producing message to %s" % out_queue.name)
        except Exception:
            logger.exception("failed producing message to %s" % out_queue.name)
            status = False
        all_delivery_reports.append(
            DeliveryReport(
                destination=out_queue.name,
                asynchronous=out_queue.producer_con.callback_delivery,
                status=status,
            )
        )
    return all_delivery_reports


def delivery_success(delivery_reports: List[DeliveryReport]) -> DeliveryReport:
    """determines whether we're going to call on_success or on_fail, or let the producer call it w/ callback
    If there is delivery to an async producer, we'll want to let it handle the callback, but there could
    be synchronous producers that failed as well.

    Producer Cases:
        - single synchronous producer
        - multi synchronous producers
        - single asynchronous producer
        - multi asynchronous producers
        - mixture of synchronous and asynchronous producers

    Order of processing:
        - if a synchronous producer failed - mark it failed
        - if async producer - wait for it
        - else mark it a success
    """

    waiting_async: int = 0
    sync_failures: int = 0
    for report in delivery_reports:
        if report.asynchronous:
            waiting_async += 1
        else:
            sync_failures = sync_failures + int(not report.status)

    if not sync_failures and not waiting_async:
        # happy path. no sync failures and no async producers
        # call on_success synchronously
        return DeliveryReport(status=True, asynchronous=False)
    elif waiting_async and not sync_failures:
        # produced asynchronously without sync fails, return the async delivery report
        # we'll let the Producer call on_success or on_fail
        return DeliveryReport(status=True, asynchronous=True)
    else:
        # had async or synchronous producer(s) failures.
        # call on_fail synchronously
        return DeliveryReport(status=False, asynchronous=False)
