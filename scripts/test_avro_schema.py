import avro.schema
from avro.io import DatumWriter, BinaryEncoder
import io

with open("../schemas/sensor_reading.avsc", "r") as f:
    schema = avro.schema.parse(f.read())

record = {
    "sensor_id": 1,
    "temperature": 32.5,
    "humidity": 85.0,
    "pressure": 1013.2,
    "timestamp": "2025-04-01 08:00:00",
    "region": "Jakarta",
    "location": {"latitude": -6.2088, "longitude": 106.8456}
}

bytes_writer = io.BytesIO()
encoder = BinaryEncoder(bytes_writer)
writer = DatumWriter(schema)  # Corrected this line
writer.write(record, encoder)  # 'writer.writer()' -> 'writer.write()'
serialized_data = bytes_writer.getvalue()

print("Serialized data size (bytes):", len(serialized_data))
