docker-compose up -d

docker exec -it kafka-kafka-broker-1-1 kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 3 \
  --partitions 30 \
  --topic global_readings

docker exec -it kafka-kafka-broker-1-1 kafka-topics --describe \
  --bootstrap-server localhost:9092 \
  --topic global_readings
