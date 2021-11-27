# Basic Example

This is the most basic example; an application that receives a list of floats in a message from Kafka. The application publishes the maximum value to the output Kafka Topic.

```python
# app.py
{!../../example/simple.py!}
```

Set a few environment variables:
```bash
KAFKA_KEY=<kafka username>
KAFKA_SECRET=<kafka password>
KAFKA_BROKERS=<host:port of the brokers>
```

And run your application with:

```bash
python app.py
```