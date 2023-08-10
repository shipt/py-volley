# Dead Letter Queues

Dead letter queues (DLQ) are special types of queues that are typically reserved for messages that have failed processing.

If enabled, Volley will publish messages, which fail either serialization or schema validation, to a specified dead letter queue. Application can also electively send a message to a dead letter queue by providing it specifying the dead letter queue by name in the functions return statement.

To configure a dead letter queue, provide it in queue configuration:


```python
config = {
    "input-topic": {
      "value": "long.name.of.kafka.input.topic",
      "profile": "confluent",
    }
    "my-dead-letter-queue": {
        "value": "long.name.of.kafka.DLQ.topic",
        "profile": "confluent-dlq",
    }
}
```

The [confluent-dlq](./profiles.md#confluent-dlq) profile disables serialization and model handling. This routes the raw message from the input topic to the dead-letter-queue.

Then specify the DLQ on Engine init:

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

Messages that fail serialization or validation will be routed to the dead-letter-queue (and never reach your application). Unhandled exceptions within the user application are NOT handled by Volley's DLQ mechanism.

<a href="https://lucid.app/publicSegments/view/8acc3ba5-93d6-4b85-9b9a-c4658684a309/image.png
" target="_blank">
    <img src="https://lucid.app/publicSegments/view/8acc3ba5-93d6-4b85-9b9a-c4658684a309/image.png" alt="DLQ">
</a>

Alternatively, your application can manually route a message to the dead-letter-queue. However, by default there is no serialization or data validation for the DLQ. This is because Volley DLQs are designed to be a close mirror of the input-queue and allow for ease of replaying of messages. Therefore, if you want to manually publish to a DLQ, you will need to manually convert your data to bytes.

```python
from pydantic import BaseModel

class myInput(BaseModel):
  myData: int


@app.stream_app
def my_app(msg: myInput) -> Union[List[Tuple[str, myInput]], bool]:
  """function that manually routes unhandled exceptions to a DLQ"""
  try:
    rando = randint(0, 1)
    1/rando
  except ZeroDivisionError:
      # send to DLQ as bytes
      output_message = msg.model_dump_json().encode("utf-8")
      return [("my-dead-letter-queue", output_message)]
  # eat the message, mark incoming message as "success"
  return True
```

Volley creates ERROR level logs whenever messages fail serialization or validation. There are also Prometheus [metrics](./metrics.md) logged each time a message is published to any queue, including dead-letter-queues. It is recommended to create alerts on these metrics to help monitor this process. For example, the below Prometheus query would result in the total number of messages that have been produced to the dead letter topic over the prior 24h time window.

```promql
increase(messages_produced_count_total{destination="my-dead-letter-queue"}[24h])
```

