import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# 1. Initialize Spark for a 16GB System
def init_spark():
    print("Initializing Spark Engine (Java 21)...")
    return SparkSession.builder \
        .appName("FinanceSparkAgent") \
        .master("local[*]") \
        .config("spark.driver.memory", "6g") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .getOrCreate()

spark = init_spark()

file_path="data/big_financial_data.csv"

def analyze_finances(file_path):
    """Example Spark function to find high-value anomalies"""
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."

    # Read data (Spark handles the 1GB+ size automatically)
    df = spark.read.csv(file_path, header=True, inferSchema=True)

    # Logic: Find transactions 3x higher than the average for that category
    # This is a 'Window Function' - a great Spark resume skill!
    from pyspark.sql.window import Window
    window_spec = Window.partitionBy("category")
    
    analysis = df.withColumn("avg_amount", F.avg("amount").over(window_spec)) \
                 .withColumn("is_outlier", F.col("amount") > (F.col("avg_amount") * 1.8))
    
    total_spending = df.select(F.sum("amount")).collect()[0][0]
    print(f"--- Total Cash Flow Processed: ${total_spending:,.2f} ---")
    
    outliers = analysis.filter(F.col("is_outlier") == True)
    
    print(f"--- Analysis Complete ---")
    outliers.show(10) # Show top 10 suspicious transactions
    return outliers

if __name__ == "__main__":
    print("--- Spark Finance Agent Online ---")
    
    # Run the analysis on the test file we just created
    analyze_finances(file_path)
    
    # This keeps the container from closing immediately
    input("\nAnalysis done. Press Enter to shut down Spark...")
    spark.stop()