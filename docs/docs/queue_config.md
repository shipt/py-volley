# Configuration

Volley's configuration centers around queues. The configurations define how you application will interact with and how Volley parses data being received/sent to each queue. Queues have names, data models, model handlers, serializers, and connectors.

It is recommended to define Volley's configuration by passing a dictionary directly the Engine initializer.

## Queue Configuration

The queue configuration object is a dictionary passed into the Volley engine at initialization. It can be defined either via a `list[QueueConfig]`, a `dict`, or a .yaml file.

## List[QueueConfig]
### ::: volley.config.QueueConfig


## Dict

The queue configuration can also be composed as `Dict[str, Dict[str, str]]`. Each key in the dictionary represents the name (alias) for the queue, and the value is a dictionary of the queue's specific configurations and accept the same attributes as documented in the `volley.QueueConfig` class.

```python
queue_config = {
    "my_alias_for_input_queue": {  # alias for the queue.
        "value": "value_for_input_queue_name",  # physical name for the queue
        "profile": "confluent",  # kafka|rsmq
        "data_model": "my.models.InputMessage",  # path to Pydantic model for validating data to/from the queue
    },
    "output-topic": {
        "value": "outgoing.kafka.topic",
        "profile": "confluent",
        "data_model": "my.models.OutputMessage"
    },
    "dead-letter-queue": {
        "value": "deadletter.kafka.topic",
        "profile": "confluent"
    },
}
```

The configuration is passed to `queue_config`

```python hl_lines="5"
app = Engine(
    input_queue="my_alias_for_queue",
    output_topics=["output-topic"],
    dead_letter_queue="dead-letter-queue",
    queue_config=queue_config
)
```
## yaml
Queue configuration can also be defined via a yml file. The below is equivalent to the example shown above. This can be useful when needing to configure multiple Volley workers, particularly when multiple workers may need to publish to the same queue. Define the queues in one place and import the configuration everywhere.


```yml
# ./my_config.yml
queues:
    my_alias_for_input_queue:
        value: value_for_input_queue_name
        profile: confluent
        data_model: my.models.InputMessage
    output-topic:
        value: outgoing.kafka.topic
        profile: confluent
        data_model: my.models.OutputMessage
    dead-letter-queue:
        value: deadletter.kafka.topic
        profile: confluent
```

Then reference the file when instantiating the application.

```python hl_lines="5"
app = Engine(
    input_queue="my_alias_for_queue",
    output_topics=["output-topic"],
    dead_letter_queue="dead-letter-queue",
    yaml_config_path="./my_config.yml"
)
```