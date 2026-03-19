from pyspark.sql import SparkSession
import os

def convert():
    # 1. Initialize Spark with enough memory for the conversion
    spark = SparkSession.builder \
        .appName("CSV-to-Parquet-Converter") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()

    csv_path = "data/big_financial_data.csv"
    parquet_path = "data/financials.parquet"

    print(f"--- Starting Conversion: {csv_path} ---")

    if not os.path.exists(csv_path):
        print(f"Error: Could not find {csv_path}. Make sure the file is in your /data folder.")
        return

    # 2. Read the CSV 
    # We set inferSchema=True once here so the Parquet file 
    # saves the correct data types (Numbers as numbers, not text).
    df = spark.read.csv(csv_path, header=True, inferSchema=True)

    # 3. Write as Parquet
    # 'overwrite' ensures that if you run this twice, it just replaces the old one.
    # We use 'snappy' compression (2026 default) to keep the file size small.
    print("Writing to Parquet... (This may take a minute for 5M rows)")
    df.write.mode("overwrite").parquet(parquet_path)

    print(f"--- Success! Data saved to {parquet_path} ---")
    
    # Optional: Print the schema to verify
    df.printSchema()
    
    spark.stop()

if __name__ == "__main__":
    convert()