from pyspark.sql import SparkSession
from pyspark.sql.functions import col, substring

# Initialize Spark session with high resource allocation
spark = SparkSession.builder \
    .appName("MigrateSensorMetricsV1") \
    .config("spark.cassandra.connection.host", "localhost") \
    .config("spark.executor.memory", "4g") \
    .config("spark.executor.cores", "2") \
    .getOrCreate()

# Read from the old table
df = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="sensor_metrics", keyspace="crdp") \
    .load()

# Derive the hour column from timestamp
df_migrated = df.withColumn("hour", substring(col("timestamp"), 1, 13))

# Write to the new table
df_migrated.write \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="sensor_metrics_v1", keyspace="crdp") \
    .mode("append") \
    .save()

spark.stop()
