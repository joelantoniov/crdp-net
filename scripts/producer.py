from confluent_kafka import avro
from confluent_kafka.avro import AvroProducer
import time

# Load Avro schema from file
with open("../schemas/sensor_reading.avsc", "r") as f:
    value_schema_str = f.read()
value_schema = avro.loads(value_schema_str)

# Producer configuration
conf = {
    'bootstrap.servers': 'kafka-broker-1:9092,kafka-broker-2:9093,kafka-broker-3:9094',
    'schema.registry.url': 'http://schema-registry:8081'
}
print(conf)

producer = AvroProducer(conf, default_value_schema=value_schema)

# Simulate sensor data
regions = ["Jakarta", "Bali"]
for i in range(1000): # Simulate 1,000 messages
    record = {
        "sensor_id": i % 100,
        "temperature": 30.0 + (i % 10),
        "humidity": 80.0 + (i % 20),
        "pressure": 1013.0 + (i % 5),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "region": regions[i % 2],
        "location": {"latitude": -6.2088 if i % 2 == 0 else -8.3405, "longitude": 106.8456 if i % 2 == 0 else 115.0920}
    }
    producer.produce(topic='global_readings', value=record)
    time.sleep(0.01) # Simulate 100 messages/sec
producer.flush()
