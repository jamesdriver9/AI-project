from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Initialize Spark
spark = SparkSession.builder.appName("Generator").getOrCreate()

print("Generating 5 Million rows of financial data...")

# Create 5 million rows (~500MB - 800MB depending on content)
df = spark.range(0, 5000000).select(
    F.col("id"),
    F.expr("uuid()").alias("transaction_id"),
    (F.rand() * 1000).alias("amount"),
    F.expr("CASE WHEN rand() > 0.5 THEN 'Food' WHEN rand() > 0.2 THEN 'Rent' ELSE 'Tech' END").alias("category")
)

# This saves it into your Windows 'data' folder via the Docker Volume
df.write.mode("overwrite").csv("data/big_financial_data.csv", header=True)

print("Done! Check your Windows 'data' folder.")
spark.stop()