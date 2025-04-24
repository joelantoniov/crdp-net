from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

# Schema Registry configuration
sr_conf = {'url': 'http://localhost:8081'}
schema_registry_client = SchemaRegistryClient(sr_conf)

# Load schema
with open("../schemas/sensor_reading.avsc", "r") as f:
    schema_str = f.read()

# Register schema
schema_registry_client.register('global_readings-value', schema_str)
