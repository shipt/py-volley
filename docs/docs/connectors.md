# Connectors

Connectors are specific implementations of producers and consumers for a data store. There are currently connectors implemented for pyRSMQ and Kafka. 

Consumers and producers handle converting the `QueueMessage` objects to whichever data type and serialization is implemented in the specfic queue. For example, the pyRSMQ implementation stores messages as `JSON`, so the pyRSMQ producer converts the message in `QueueMessage` to JSON, then places the message on the queue. Likewise, pyRMSQ consumer read from JSON and convert to `QueueMessage`.

Components consume from one queue and produce to zero or many queues. Volley consumers and produces adhere to a consistent interface to conduct the following operations on any of the supported queues. These interfaces are designed in [Consumer and Producer](./volley/connectors/base.py) base classes.

Producers:

- `produce` - place a message on the queue.

- `shutdown` - gracefully disconnect the producer.

Consumers:

- `consume` - pull a message off the queue.

- `delete` - delete a message on the queue.

- `on_fail` - operation to conduct if a component worker fails processing a message. For example, place the message back on the queue, rollback a transaction, etc.

- `shutdown` - gracefully disconnect the consumer.

# Supported Connectors

Queues are the broker and backend that handle messages. Volley has built in support for two types of queue technoloigies; RSMQ and Kafka.

### 1. [pyRSMQ](https://github.com/mlasevich/PyRSMQ)

The python implementation of the [RSMQ](https://github.com/smrchy/rsmq) project. It is lightweight but full featured message queue system built on Redis. It provides clean interface to producing and consuming messages from a queue. It only supports strict FIFO - you cannot modify or update a message on the queue once it is produced. The number of messages that can exist in the queue is limited by the amount of memory available to Redis.

Environment variables:
```bash
REDIS_HOST=host_to_run_rsmq
```

### 2. Kafka - [confluent_kafka](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html) and [pyshipt-streams](https://github.com/shipt/pyshipt-streams)

Environment variables:
```bash
KAFKA_CONSUMER_GROUP=<kafka_consumer_group>
KAFKA_KEY=<kafka username>
KAFKA_SECRET=<kafka password>
KAFKA_BROKERS=<host:port of the brokers>
```

All [librdkafka configurations](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md) can be passed through to the connector.

```yml
- name: output_topic
  value: output.kafka.topic.name
  type: kafka
  schema: volley.data_models.ComponentMessage
  config:
    bootstrap.servers: kafka_broker_host:9092
```

# Extending Connectors with Custom Plugins

Users can write their own connectors as needed. This is done by subclassing `volley.connects.base.Consumer & Producer`, then registering the connectors in the engine configuration.

First, let's build a Consumer and Producer for Postgres.

## Build the plugin

```python
# my_plugin.py
{!../../example/plugins/my_plugin.py!}
```

The consumer has the specific implementations for `consume`, `delete_message`, `on_fail`, and `shutdown`. The producer implements `produce` and `shutdown`.


## Register the plugin with Volley's configuration

Like all configuration, they can be specified in either `yaml` or a `dict` passed directly to `volley.engine.Engine` (but not both).

```yml
# ./my_volly_config.yml
- name: postgres_queue
  value: pg_queue_table
  type: postgres
  schema: volley.data_models.ComponentMessage
  producer: example.plugins.my_plugin.MyPGProducer
  consumer: example.plugins.my_plugin.MyPGConsumer
```

Is is equivalent to:

```python
config = {
    "postgres_queue": {
        "value": "pg_queue_table",
        "type": "postgres",
        "schema": "volley.data_models.ComponentMessage,
        "producer": "example.plugins.my_plugin.MyPGProducer"
        "consumer": "example.plugins.my_plugin.MyPGConsumer "
    }
}
```

A complete example using this plugin is provided [here](advanced_example.md)
