# Volley

Volley is a lightweight message stream processor for Python.

Repository: [https://github.com/shipt/volley](https://github.com/shipt/volley)

Use Volley to quickly build applications that need to poll streaming sources like Kafka, then process the data is receives, and publish results to one or many other streaming destinations.

Volley applications, "workers", are implemented as a function decorated with an instance of the `volley.engine.Engine`. A worker consumes from one queue and can publish to zero or many queues.

A worker function takes in input of type: `ComponentMessage`, which is a Pydantic model that accepts extra attributes. This model defines the schema of messages on the `input_queue`. The component function can process and modify that object to meet its needs.

Volley is production-ready, and provides the following:

- Prometheus [Metrics](./metrics.md) for system observability
- Data validation via [Pydantic](https://pydantic-docs.helpmanual.io/)
- Built-in support for both Kafka and [pyRSMQ](https://github.com/mlasevich/PyRSMQ)(Redis)
- Serialization in JSON and soon [MessagePack](https://msgpack.org/index.html)
- Optional [dead-letter-queues](deadletterqueue.md) for serialization and schema validation failures