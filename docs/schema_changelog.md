## 2025-04-24: Transition to sensor_metrics_v1
- **Change**: Moved from `sensor_metrics` to `sensor_metrics_v1` due to schema update (added `hour` to partition key).
- **Reason**: Direct table renaming not supported in Cassandra; updated application to use new table.
- **Migration**: Data migrated to `sensor_metrics_v1` using Spark.
- **Backup**: Original `sensor_metrics` retained with comment 'Backup table as of 2025-04-24, replaced by sensor_metrics_v1'.
- **Impact**: No downtime; pipeline now uses `sensor_metrics_v1`.
