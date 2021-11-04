import os
import time

import confluent_kafka.admin

# time for Kafka broker to init
time.sleep(5)

input_topic = "localhost.bus.ds-marketplace.v1.bundle_engine_input"
output_topic = "localhost.bus.ds-marketplace.v1.bundle_engine_output"
brokers = os.environ["KAFKA_BROKERS"]
conf = {"bootstrap.servers": brokers}
admin = confluent_kafka.admin.AdminClient(conf)
topics = [confluent_kafka.admin.NewTopic(x, 1, 1) for x in [input_topic, output_topic]]
admin.create_topics(topics)
# TODO: can we stop here and validate topics are created before proceeding?
