import os
import shutil
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# 1. SETUP SPARK
spark = SparkSession.builder.appName("DataRefresher").getOrCreate()
output_path = "data/financials.parquet"

print("🚀 Starting fresh data generation...")

# 2. GENERATE 5 MILLION ROWS (In Memory)
# This creates a simple DataFrame so we have something to work with
df = spark.range(0, 5000000).withColumnRenamed("id", "transaction_id")

# 3. ADD YOUR COLUMNS (Category, Amount, Date)
categories = ["Food", "Rent", "Tech", "Transport", "Utilities"]

# Correct functional approach for PySpark
df = df.withColumn("amount", F.round(F.rand() * 1000, 2)) \
       .withColumn("category", F.element_at(
           F.array([F.lit(c) for c in categories]), 
           (F.rand() * 5 + 1).cast("int")
       )) \
       .withColumn("date", F.expr("date_add(current_date(), -cast(rand() * 365 as int))"))

# 4. MANUALLY CLEAN THE DIRECTORY (The Windows/Docker Fix)
if os.path.exists(output_path):
    print(f"🗑️ Cleaning old path: {output_path}")
    shutil.rmtree(output_path)

# 5. WRITE THE NEW DATA
print("💾 Writing 5,000,000 rows to Parquet with 'date' column...")
df.write.parquet(output_path)

print("✅ SUCCESS: data/financials.parquet is ready with the new schema!")