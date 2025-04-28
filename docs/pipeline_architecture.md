# CRDP-Net Pipeline Architecture

## Full-Scale Design (5PB/Day, 500 Regions)

### Overview
- **Volume**: 1TB/day 
- **Regions**: 50 (e.g., Jakarta, Bali, New York).
- **Components**:
  - Kafka: 16 brokers, 58 partitions.
  - Spark: 10 nodes (EMR clusters in Asia, North America, Europe).
  - Cassandra: 50 nodes (multi-datacenter).
  - Grafana: Cloud deployment with Presto for querying.

### Scheduler (Airflow)
- **Purpose**: Orchestrates scripts across regions and clusters.
- **Tasks**:
  - `streaming_job.py`: Runs for each region (50 instances).
  - `analyze_watermark.py`: Runs daily to tune watermark.
- **Deployment**: AWS MWAA, 10 workers.

### Regional and Time Zone Handling
- **Regions**: Each Spark job filters by region (e.g., `--region Jakarta`).
- **Time Zones**: UTC timestamps for consistency; Grafana displays local time.

### Performance
- **Latency**: ~7 minutes (needs optimization for 5-minute KPI).
- **Next Steps**: Add low-latency alerting pipeline (e.g., Flink).

### Monitoring
- Airflow UI, Spark UI, DataStax OpsCenter, Grafana system dashboards.
