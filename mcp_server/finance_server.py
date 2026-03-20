from fastmcp import FastMCP
import os
from pyspark.sql import SparkSession

# 1. Initialize Spark once
print("🚀 STARTING DYNAMIC MULTI-SOURCE ENGINE...")
spark = SparkSession.builder \
    .appName("UniversalAnalysisEngine") \
    .master("local[*]") \
    .getOrCreate()

mcp = FastMCP("FinanceEngine")

def load_all_tables():
    """Internal helper to scan /app/data and register every .parquet file as a Spark view."""
    data_path = "/app/data"
    registered = []
    
    if not os.path.exists(data_path):
        print(f"⚠️ Warning: {data_path} not found.")
        return []
        
    files = [f for f in os.listdir(data_path) if f.endswith(".parquet")]
    
    for item in files:
        table_name = item.replace(".parquet", "")
        full_path = os.path.join(data_path, item)
        
        try:
            # Overwrite the view with fresh data from disk
            df = spark.read.parquet(full_path)
            df.createOrReplaceTempView(table_name)
            
            # Force Spark to clear metadata cache for this specific table
            spark.catalog.refreshTable(table_name)
            registered.append(table_name)
            print(f"✅ Registered table: {table_name}")
        except Exception as e:
            print(f"❌ Failed to load {item}: {e}")
            
    return registered

# --- TOOL 1: LIST TABLES ---
@mcp.tool()
async def list_available_tables() -> str:
    """Returns a list of all data tables currently available in the Spark engine."""
    try:
        tables = load_all_tables()
        if not tables:
            return "No tables found in /app/data. Ensure .parquet files are in the data folder."
        return f"Available tables: {', '.join(tables)}"
    except Exception as e:
        return f"Error listing tables: {str(e)}"

# --- TOOL 2: DYNAMIC SCHEMA TOOL ---
@mcp.tool()
async def get_table_schema(table_name: str) -> str:
    """
    Use this tool to see the columns and data types for a specific table.
    Example: get_table_schema('logistics')
    """
    try:
        # Refresh views to make sure we aren't looking at old metadata
        load_all_tables()
        
        # Check if table exists in Spark catalog
        if not spark.catalog.tableExists(table_name):
            available = [t.name for t in spark.catalog.listTables()]
            return f"Error: Table '{table_name}' not found. Available tables are: {available}"
            
        schema_info = spark.table(table_name).schema.simpleString()
        return f"Schema for '{table_name}': {schema_info}"
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"

# --- TOOL 3: UNIVERSAL QUERY TOOL ---
@mcp.tool()
async def query_spark(query: str) -> str:
    """
    Execute a Spark SQL query against any registered table.
    Example: SELECT * FROM logistics WHERE origin_city = 'London'
    """
    try:
        # Final refresh before query execution
        load_all_tables()
        
        print(f"📥 EXECUTING SQL: {query}")
        result_df = spark.sql(query).limit(10)
        result_json = result_df.toJSON().collect()
        
        if not result_json:
            return "Query successful: No records found."
            
        return "\n".join(result_json)
        
    except Exception as e:
        print(f"❌ SPARK SQL ERROR: {str(e)}")
        return f"Spark SQL Error: {str(e)}. Tip: Verify table/column names with list_available_tables and get_table_schema."

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)