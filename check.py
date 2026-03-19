from pyspark.sql import SparkSession
from pyspark.sql.functions import sum

# 1. Start Spark
spark = SparkSession.builder.appName("ManualCheck").getOrCreate()

# 2. Load your 5 million rows
df = spark.read.parquet("data/financials.parquet")

# 3. The Query: Filter for 'Rent' and Sum the 'amount' column
total_rent = df.filter(df.category == "Rent").select(sum("amount")).collect()[0][0]

print(f"\n💰 TOTAL SPEND ON RENT: ${total_rent:,.2f}")