# ML Bundle Engine
The ML bundle engine is an event driven series of processes & queues. 
The engine intakes a Kafka message from the bundle request topic, makes a prediction with an ML model, runs an optimizer and outputs to a Kafka topic.

![Engine Architecture](./docs/assets/ml-bundling-architecture.png)

## Maintainer(s)
 - @Jason
 - @AdamH

## Notes

# Visibility timeout - how long until the message should be placed back on the queue. This is basically the timeout for the component to do its thing. Example, vt=10, if component pulls the message off and doesnt delete the message within 10 seconds, the message will go back onto the queue and another worker can pull it off.

# Delay - how long to wait before doing the actual action