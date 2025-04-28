from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, avg, lit, unix_timestamp, current_timestamp
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, StringType, DoubleType
import argparse
import joblib
import numpy as np
from get_rainfall import get_rainfall

# Parse region argument
parser = argparse.ArgumentParser()
parser.add_argument('--region', required=True, help='Region to process')
args = parser.parse_args()
region = args.region

# Initialize Spark session
spark = SparkSession.builder \
    .appName(f"CRDPNetStreaming_{region}") \
    .config("spark.cassandra.connection.host", "cassandra-cluster") \
    .config("spark.streaming.kafka.maxRatePerPartition", "10000") \
    .getOrCreate()

# Load AI model
model = joblib.load("s3://crdp-net/models/flood_risk_model.pkl")
broadcast_model = spark.sparkContext.broadcast(model)

# Define schema
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
    .option("kafka.bootstrap.servers", "kafka-cluster:9092") \
    .option("subscribe", "global_readings") \
    .load()

# Parse JSON messages
df = df.selectExpr("CAST(value AS STRING) as json") \
       .select(from_json(col("json"), schema).alias("data")) \
       .select("data.*")

# Filter by region
df = df.filter(col("region") == region)

# Compute 5-minute aggregates (in UTC)
aggregates = df.withWatermark("timestamp", "15 minutes") \
               .groupBy(
                   window(col("timestamp"), "5 minutes"),
                   col("region")
               ).agg(
                   avg("temperature").alias("avg_temperature"),
                   avg("humidity").alias("avg_humidity"),
                   avg("pressure").alias("avg_pressure")
               )

# Add hour and timestamp columns
aggregates = aggregates.withColumn("hour", col("window.start").cast("string").substr(1, 13)) \
                       .withColumn("timestamp", col("window.start").cast("string")) \
                       .drop("window")

# Predict flood risk
def predict_flood_risk(temp, hum, press, region, timestamp):
    rainfall = get_rainfall(region, timestamp)
    features = np.array([[temp, hum, press, rainfall]])
    prediction = broadcast_model.value.predict_proba(features)[0][1]
    return float(prediction)

predict_udf = udf(predict_flood_risk, DoubleType())
aggregates = aggregates.withColumn(
    "flood_risk",
    predict_udf(
        col("avg_temperature"),
        col("avg_humidity"),
        col("avg_pressure"),
        col("region"),
        col("timestamp")
    )
)

# Write to Cassandra
query = aggregates.writeStream \
    .format("org.apache.spark.sql.cassandra") \
    .option("keyspace", "crdp") \
    .option("table", "sensor_metrics_v1") \
    .outputMode("update") \
    .start()

query.awaitTermination()
