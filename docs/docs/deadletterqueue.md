# Dead Letter Queues

Dead letter queues (DLQ) are special types of queues that are typically reserved for messages that have failed processing.

If enabled, Volley will publish messages, which fail either serialization or schema validation, to a specified dead letter queue. Application can also electively send a message to a dead letter queue.

To configure a dead letter queue, provide it in queue configration (either yaml or dict):


```yml
# ./my_volly_config.yml
input-topic:
  value: long.name.of.kafka.input.topic
  type: kafka
my-dead-letter-queue:
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

<a href="https://lucid.app/publicSegments/view/8acc3ba5-93d6-4b85-9b9a-c4658684a309/image.png
" target="_blank">
    <img src="https://lucid.app/publicSegments/view/8acc3ba5-93d6-4b85-9b9a-c4658684a309/image.png" alt="DLQ">
</a>


Volley creates ERROR level logs whenever messages fail serialization or validation. There are also Prometheus [metrics](./metrics.md) logged each time a message is published to any queue, including dead-letter-queues. It is recommended to create alerts on these metrics to help monitor this process. For example, the below Prometheus query would result in the total number of messages that have been produced to the dead letter topic over the prior 24h time window.

```promql
increase(messages_produced_count_total{destination="my-dead-letter-queue"}[24h])
```

