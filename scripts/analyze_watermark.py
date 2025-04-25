from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, unix_timestamp, percentile_approx
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, StringType

# Initialize Spark session
spark = SparkSession.builder \
    .appName("WatermarkAnalysis") \
    .getOrCreate()

# Define schema for Kafka messages (same as streaming_job.py)
schema = StructType([
    StructField("sensor_id", IntegerType()),
    StructField("temperature", FloatType()),
    StructField("humidity", FloatType()),
    StructField("pressure", FloatType()),
    StructField("timestamp", StringType()),
    StructField("region", StringType()),
    StructField("location", StructType([
        StructField("latitude", FloatType()),
        StructField("longitude", FloatType())
    ]))
])

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094") \
    .option("subscribe", "global_readings") \
    .load()

# Parse JSON messages
df = df.selectExpr("CAST(value AS STRING) as json") \
       .select(from_json(col("json"), schema).alias("data")) \
       .select("data.*")

# Calculate lateness (processing time - event time) in seconds
lateness_df = df.withColumn("event_time", unix_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss")) \
                .withColumn("processing_time", unix_timestamp(current_timestamp())) \
                .withColumn("lateness_seconds", col("processing_time") - col("event_time"))

# Compute statistics on lateness
stats = lateness_df.groupBy().agg(
    percentile_approx("lateness_seconds", 0.5).alias("median_lateness"),
    percentile_approx("lateness_seconds", 0.95).alias("p95_lateness"),
    percentile_approx("lateness_seconds", 0.99).alias("p99_lateness"),
    percentile_approx("lateness_seconds", 0.999).alias("p999_lateness")
)

# Write statistics to console (for analysis)
query = stats.writeStream \
    .format("console") \
    .outputMode("complete") \
    .start()

query.awaitTermination()
