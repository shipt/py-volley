# Dead Letter Queues

Dead letter queues (DLQ) are special types of queues that are typically reserved for messages that have failed processing.

If enabled, Volley will publish messages, which fail either serialization or schema validation, to a specified dead letter queue. Application can also electively send a message to a dead letter queue.

To configure a dead letter queue, provide it in queue configration (either yaml or dict):


```yml
# ./my_volly_config.yml
- name: input-topic
  value: long.name.of.kafka.input.topic
  type: kafka
- name: dead-letter-queue
  value: long.name.of.kafka.DLQ.topic
  type: kafka
```

or alternatively:

```python
config = {
    "my-dead-letter-queue": {
        "value": "long.name.of.kafka.topic",
        "type": "kafka",
    }
}
```

Then specify the queue on Engine init:

```python
from volley.engine import Engine

app = Engine(
    app_name="my_app",
    input_queue="input-topic,
    output_queue=None,
    dead_letter_queue="my-dead-letter-queue"  # this enables the DLQ
    queue_config=config
)
```

Messages that fail serialization or validation will be routed to the dead-letter-queue (and never reach the function). Alternatively, your application can specify a message be routed to the dead-letter-queue.

```python
from random import randint

from volley.data_models import ComponentMessage

@app.stream_app
def my_app(msg: ComponentMessage) -> Optional[List[Tuple[str, ComponentMessage]]]:
    """a function that randomly sends messages to DLQ or eats the message"""
    rando = ranint(0, 100)

    if rando > 50:
        # send to DLQ
        output = [("my-dead-letter-queue", msg)]
    else:
        # eat the message
        output = None
    return output
```

Volley creates WARNING level logs whenever messages fail serialization or validation. There are also Prometheus metrics logged each time a message is published to any queue, including dead-letter-queues. It is recommended to create alerts on these metrics to help monitor this process.

```promql
increase(messages_produced_count_total{destination="my-dead-letter-queue"}[24h])
```

