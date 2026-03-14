from src.data_loader import load_financial_data

def run_pipeline():
    print("--- 🚀 Starting Anomaly Detection Pipeline ---")
    
    # 1. Name of your synthetic data file
    data_file = "financial_data.csv"
    
    try:
        # 2. Call the logic sitting in src/data_loader.py
        df = load_financial_data(data_file)
        
        # 3. Print the 'Head' (First 5 rows)
        print("\n✅ DATA CONNECTION SUCCESSFUL")
        print("-" * 30)
        print("FIRST 5 ROWS OF DATA:")
        print(df.head())
        print("-" * 30)
        
        # 4. Print the 'Shape'
        print(f"Dataset Dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
        
    except Exception as e:
        print(f"❌ Pipeline Error: {e}")

if __name__ == "__main__":
    run_pipeline()

print(run_pipeline)