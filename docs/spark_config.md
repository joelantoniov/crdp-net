# Spark Configuration

## 2025-04-25: Watermark Tuning
- **Analysis**: Ran `analyze_watermark.py` to measure lateness of Kafka events.
- **Results**:
  - Median lateness: 5 minutes.
  - 95th percentile: 20 minutes.
  - 99th percentile: 25 minutes.
  - 99.9th percentile: 28.3 minutes.
- **Decision**: Set watermark to 15 minutes, capturing 95% of events while ensuring windows close within ~15 minutes of their end time.
- **Impact**: Balances data completeness with the 5-minute alerting KPI (needs further tuning for production).
