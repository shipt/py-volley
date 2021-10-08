# ML Bundle Engine
The ML bundle engine is an event driven series of processes & queues. 
The engine intakes a Kafka message from the bundle request topic, makes a prediction with an ML model, runs an optimizer and outputs to a Kafka topic.

![Engine Architecture](./docs/assets/ml-bundling-architecture.png)

## Maintainer(s)
 - @Jason
 - @AdamH

## Run locally

`docker-compose up`

