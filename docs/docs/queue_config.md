# Configuration

Volley's configuration center's around queues. Queues have names, types, schemas, serializers, and connectors. These all have default values, but can also be configured.

It is recommended to define Volley's configuration by passing a dictionary directly the Engine initializer.

## Queue Configuration

### Attributes

`name`
: (str) - *required* : Alias for the queue and how the developer references queues to consume from or produce to. For example, "input-topic". In the dictionary config, this is the parent key; cf. [example](#example)

`value` 
: (str) - *required* : The system name for a queue. For example, the name of a Kafka topic (prd.my.long.kafka.topic.name) or name of a RSMQ queue.

`type`
: (str) - *required* : Either `kafka|rsmq`. Pertains to the type of connector required to produce and consume from the queue.

`schema`
: (str) - *optional* : Defaults to `volley.data_models.ComponentMessage`. Path to the Pydantic model used for data validation. When default is used, Volley will only validate that messages can be successfully converted to a Pydantic model or dictionary.

`serializer`
: (str) - *optional* : Defaults to `volley.serializers.OrJsonSerializer`. Path to the serializer.

`producer`
: (str) - *optional* : Used for providing a custom producer connector. Overrides the producer pertaining to that provided in `type`. Provide the dot path to the producer class. e.g. for Kafka, defaults to `volley.connectors.kafka.KafkaProducer`; cf. [Extending Connectors](connectors.md#extending-connectors-with-plugins).

`consumer`
: (str) - *optional* : Used for providing a custom consumer connector. Overrides the consumer pertaining to that provided in `type`. Provide the dot path to the consumer class. e.g. for Kafka, defaults to `volley.connectors.kafka.KafkaConsumer`; cf. [Extending Connectors](connectors.md#extending-connectors-with-plugins).

`config`
: (dict) - *optional* : Any configuration to be passed directly to the queue connector. For example, all [librdkafka configurations](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md) can be passed through to the connector via a dictionary here.


## Example

Let's define configuration for three queues; one input queue, an output queue, and a dead letter queue.

```python
queue_config = {
    "my_alias_for_input_queue": {  # alias for the queue.
        "value": "value_for_input_queue_name",  # physical name for the queue
        "type": "kafka",  # kafka|rsmq
        "schema": "my.models.InputMessage",  # path to Pydantic model for validating data to/from the queue
    },
    "output-topic": {
        "value": "outgoing.kafka.topic",
        "type": "kafka",
        "schema": "my.models.OutputMessage"
    },
    "dead-letter-queue": {
        "value": "deadletter.kafka.topic",
        "type": "kafka"
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

Queue configuration can also be defined via a yml file. The below is equivalent to the example shown above. This can be useful when needing to configure multiple Volley workers, particularly when multiple workers may need to publish to the same queue. Define the queues in one place and import the configuration everywhere.


```yml
# ./my_config.yml
queues:
  - name: my_alias_for_input_queue
    value: value_for_input_queue_name
    type: kafka
    schema: my.models.InputMessage
  - name: output-topic
    value: outgoing.kafka.topic
    type: kafka
    schema: my.models.OutputMessage
  - name: dead-letter-queue
    value: deadletter.kafka.topic
    type: kafka
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