# Advanced Example

Run the pre-built example from the root level of this repository with 

```bash
make run.example
```

You will need `docker`, and `docker-compose` installed on your machine. Kafka, Redis, and Postgres are each spawned in their own Docker containers defined in `docker-compose.yml`.


The example consists of the Volley workers, which are functions described below.

- `./example/external_data_producer.py` publishes sample data to `input-topic` Kafka topic.
- `./example/input_worker.py` consumes from `input-topic` and publishes to `redis_queue`, RSMQ queue. 
- `./example/middle_worker.py` consumes from `redis_queue` RSMQ and publishes to both `output-topic` Kafka topic, and uses the custom Postgres plugin for publishing to `postgres_queue`, which is a table. middle-worker randomly sends messages back to the input-topic.
- `./example/external_data_consumer.py` consumes from `output-topic` and logs to console.


<a href="https://lucid.app/publicSegments/view/7a08a0e6-53ca-44b1-8ddf-1ee04a963e07/image.png" target="_blank">
    <img src="https://lucid.app/publicSegments/view/7a08a0e6-53ca-44b1-8ddf-1ee04a963e07/image.png" alt="Test">
</a>
