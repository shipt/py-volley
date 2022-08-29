# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import builtins
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

from prometheus_client import Counter, Summary, start_http_server

from volley.concurrency import run_async, run_worker_function
from volley.config import QueueConfig, load_yaml
from volley.data_models import QueueMessage
from volley.logging import logger
from volley.models.base import message_model_handler
from volley.profiles import ConnectionType, Profile, construct_profiles
from volley.queues import DLQNotConfiguredError, Queue, construct_queue_map
from volley.transport import DeliveryReport, delivery_success, produce_handler
from volley.util import FuncEnvelope, GracefulKiller

# enables mocking the infinite loop to finite
RUN_ONCE = False


HEARTBEAT = Counter("heartbeats", "Application liveliness")
MESSAGE_CONSUMED = Counter(
    "messages_consumed_count", "Messages consumed from input", ["volley_app", "status"]
)  # success or fail
PROCESS_TIME = Summary("process_time_seconds", "Time spent running a process", ["volley_app", "process_name"])


@dataclass
class Engine:
    """Initializes the Volley application and prepares the main decorator
    Attributes:
        app_name: Name of the application. Added as a label to all logged metrics
        input_queue:
            Name of the input queue.
            Corresponds to the name of one queue defined in queue_config or yaml_config_path
        output_queues: List of queues the application needs to be able to publish to.
            Not required if the application does not produce anywhere!
        dead_letter_queue: Points to the queue in configuration used as the dead letter queue.
        poll_interval_seconds: globally set time to to halt between polls on the consumer
        queue_config: either a list of QueueConfig (one for each queue) or a dictionary of queue configurations.
            Must provide one of queue_config or yaml_config_path
        yaml_config_path: path to a yaml config file.
            Must provide one of yaml_config_path or queue_config
    Raises:
        NameError: input_queue, dead_letter_queue or output_queues
            reference a queue that does not exist in queue configuration
    Returns:
        Engine: Instance of the engine with a prepared `stream_app` decorator
    """

    input_queue: str
    output_queues: List[str] = field(
        default_factory=list,
    )

    app_name: str = "volley"
    dead_letter_queue: Optional[str] = None
    queue_config: Union[List[QueueConfig], Dict[str, Any], None] = None
    yaml_config_path: str = "./volley_config.yml"
    metrics_port: Optional[int] = 3000
    poll_interval_seconds: float = 1.0

    queue_map: Dict[str, Queue] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Validates configuration and initializes queue configs
        Database connections are initialized within stream_app decorator
        """
        self.killer: GracefulKiller = GracefulKiller()

        if self.output_queues == []:
            logger.warning("No output queues provided")

        # queue config can come in three ways
        # 1. List[QueueConfig] , list of typed configurations, one for each queue
        # 2. dictionary, queueName: configurations
        # 3. yaml file

        if isinstance(self.queue_config, list):
            cfg = {x.name: x.to_dict() for x in self.queue_config}
        elif isinstance(self.queue_config, dict):
            cfg = self.queue_config
        else:
            logger.info("loading configuration from %s", self.yaml_config_path)
            cfg = load_yaml(file_path=self.yaml_config_path)["queues"]

        # handle DLQ
        if self.dead_letter_queue is not None:
            # if provided by user, DLQ becomes a producer target
            # flag the queue using the DLQ profile
            if self.dead_letter_queue not in cfg:
                raise KeyError(f"{self.dead_letter_queue} not present in configuration")
            else:
                self.output_queues.append(self.dead_letter_queue)
        else:
            logger.warning("DLQ not provided. Application will crash on schema violations")

        # cfg can contain configs for more queues that the app needs
        # filter out queues that are not required by app
        cfg = {k: v for k, v in cfg.items() if k in [self.input_queue] + self.output_queues}

        # validate input_queue, output_queues, and DLQ (optional) are valid configurations
        for q in [self.input_queue] + self.output_queues:
            if q not in cfg:
                raise KeyError(f"Queue '{q}' not found in configuration")

        # tag queues with type (how app intends to use it)
        cfg[self.input_queue]["connection_type"] = ConnectionType.CONSUMER
        for qname in self.output_queues:
            cfg[qname]["connection_type"] = ConnectionType.PRODUCER

        # load profiles
        profiles: Dict[str, Profile] = construct_profiles(cfg)
        # create queue_map from profiles
        self.queue_map = construct_queue_map(profiles, cfg)

        logger.info("Queues initialized: %s", list(self.queue_map.keys()))

    def stream_app(  # noqa: C901
        self,
        func: Callable[..., Union[Awaitable[Any], List[Tuple[str, Any]], List[Tuple[str, Any, Dict[str, Any]]], bool]],
    ) -> Callable[..., None]:
        """Main decorator for applications"""

        _func = FuncEnvelope(func)

        @run_async
        @wraps(func)
        async def run_component() -> None:
            if self.metrics_port is not None:
                start_http_server(port=self.metrics_port)
            # the component function is passed in as `func`
            # first setup the connections to the input and outputs queues that the component will need
            # we only want to set these up once, before the component is invoked

            # initialize connections to each queue, and schemas
            self.queue_map[self.input_queue].connect(con_type=ConnectionType.CONSUMER)
            # we only want to connect to queues passed in to Engine()
            # there can be more queues than we need defined in the configuration yaml
            for out_q_name in self.output_queues:
                self.queue_map[out_q_name].connect(con_type=ConnectionType.PRODUCER)

            # queue connections were setup above. now we can start to interact with the queues
            # alias for input connection readability
            input_con: Queue = self.queue_map[self.input_queue]

            # if asynchronous producer, give the consumer's "on_success" method to the producer
            for qname in self.output_queues:
                producer_con = self.queue_map[qname].producer_con
                if producer_con.callback_delivery:
                    producer_con.init_callbacks(consumer=self.queue_map[self.input_queue].consumer_con)

            logger.info("Starting Volley application: %s", self.app_name)
            while not self.killer.kill_now:
                HEARTBEAT.inc()
                _start_time = time.time()
                # read message off the specified queue
                in_message: Optional[QueueMessage] = input_con.consumer_con.consume()
                if in_message is None:
                    # if no messages, handle poll interval
                    # TODO: this should be dynamic with some sort of backoff
                    logger.debug("No messages - sleeping POLL_INTERVAL=%s", self.poll_interval_seconds)
                    time.sleep(self.poll_interval_seconds)
                    continue

                # typing for producing
                outputs: Union[List[Tuple[str, Any]], List[Tuple[str, Any, Dict[str, Any]]], bool] = False

                data_model, consume_status = message_model_handler(
                    message=in_message.message,
                    schema=input_con.data_model,
                    model_handler=input_con.model_handler,
                    serializer=input_con.serializer,
                )

                if consume_status:
                    # happy path
                    MESSAGE_CONSUMED.labels(volley_app=self.app_name, status="success").inc()
                elif self.dead_letter_queue is not None and self.dead_letter_queue in self.queue_map:
                    outputs = [(self.dead_letter_queue, data_model)]
                    MESSAGE_CONSUMED.labels(volley_app=self.app_name, status="fail").inc()
                else:
                    # things have gone wrong w/ the message and no DLQ configured
                    MESSAGE_CONSUMED.labels(volley_app=self.app_name, status="fail").inc()
                    raise DLQNotConfiguredError(f"Deserializing {in_message.message} failed")

                # component processing
                if not outputs:
                    # this is happy path
                    # if outputs have been assigned it means this message is destined for a DLQ
                    _start_main = time.time()
                    outputs = await run_worker_function(
                        app_name=self.app_name,
                        f=_func,
                        message=data_model,
                        ctx=in_message.message_context,
                    )
                    _fun_duration = time.time() - _start_main
                    PROCESS_TIME.labels(volley_app=self.app_name, process_name="component").observe(_fun_duration)

                delivery_report: DeliveryReport
                if isinstance(outputs, builtins.bool):
                    # if func returns a bool, its just a bool and nothing more
                    # there is no "producer" in this model.
                    # Just mark the consumed message as either success or fail
                    delivery_report = DeliveryReport(status=outputs, asynchronous=False)

                else:
                    delivery_reports: list[DeliveryReport] = produce_handler(
                        outputs=outputs,
                        queue_map=self.queue_map,
                        app_name=self.app_name,
                        input_name=input_con.name,
                        message_context=in_message.message_context,
                    )
                    delivery_report = delivery_success(delivery_reports)
                if delivery_report.status is True and not delivery_report.asynchronous:
                    # asynchronous delivery reports are handled within the Producer's callback
                    # synchrnous delivery reports are handled here
                    input_con.consumer_con.on_success(
                        message_context=in_message.message_context,
                    )
                elif not delivery_report.asynchronous:
                    input_con.consumer_con.on_fail(
                        message_context=in_message.message_context,
                    )
                _duration = time.time() - _start_time
                PROCESS_TIME.labels(volley_app=self.app_name, process_name="cycle").observe(_duration)

                if RUN_ONCE:
                    # for testing purposes only - mock RUN_ONCE
                    break

            self.shutdown()

        # used for unit testing as a means to access the wrapped component without the decorator
        run_component.__wrapped__ = func  # type: ignore

        return run_component

    def shutdown(self) -> None:
        """graceful shutdown of all queue connections"""
        logger.info("Shutting down %s, %s", self.app_name, self.queue_map[self.input_queue].value)
        for q_name in self.output_queues:
            out_queue = self.queue_map[q_name]
            logger.info("Shutting down %s, %s", self.app_name, out_queue.value)
            out_queue.producer_con.shutdown()
            logger.info("%s, %s shutdown complete", self.app_name, q_name)
        self.queue_map[self.input_queue].consumer_con.shutdown()
        logger.info("Shutdown %s complete", self.app_name)
