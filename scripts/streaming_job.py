from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, avg, lit
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, StringType, DoubleType

# Initialize Spark session
spark = SparkSession.builder \
    .appName("CRDPNetStreaming") \
    .config("spark.cassandra.connection.host", "localhost") \
    .getOrCreate()

# Define schema for Kafka messages
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

# Compute 5-minute aggregates
aggregates = df.withWatermark("timestamp", "10 minutes") \
               .groupBy(
                   window(col("timestamp"), "5 minutes"),
                   col("region")
               ).agg(
                   avg("temperature").alias("avg_temperature"),
                   avg("humidity").alias("avg_humidity"),
                   avg("pressure").alias("avg_pressure"),
                   lit(0.5).alias("flood_risk")  # Placeholder for AI model
               )

# Add hour column for Cassandra partition key
aggregates = aggregates.withColumn("hour", col("window.start").cast("string").substr(1, 13)) \
                       .withColumn("timestamp", col("window.start").cast("string")) \
                       .drop("window")

# UDF to predict flood risk
def predict_flood_risk(temp, hum, press, region, timestamp):
    rainfall = get_rainfall(region, timestamp)
    features = np.array([[temp, hum, press, rainfall]])
    prediction = broadcast_model.value.predict_proba(features)[0][1]  # Probability of flood
    return float(prediction)

predict_udf = udf(predict_flood_risk, DoubleType())

# Add flood risk prediction
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
    .option("table", "sensor_metrics") \
    .outputMode("update") \
    .start()

query.awaitTermination()
