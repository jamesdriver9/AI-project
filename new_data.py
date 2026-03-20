import pandas as pd
import numpy as np
import os
import shutil

# 1. Setup the directory
data_dir = './data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 2. CREATE SHARED KEYS (The Bridge)
# We create 1,000 unique transaction IDs to link the tables
shared_ids = [f'TXN_{i:04d}' for i in range(1000)]

# 3. GENERATE FINANCIALS DATA
df_fin = pd.DataFrame({
    'transaction_id': shared_ids,
    'amount': np.random.uniform(500.0, 50000.0, 1000).round(2),
    'category': np.random.choice(['Electronics', 'Furniture', 'Apparel', 'Medical'], 1000),
    'date': pd.date_range(start='2026-01-01', periods=1000).strftime('%Y-%m-%d')
})

# 4. GENERATE LOGISTICS DATA (Linked via transaction_id)
df_log = pd.DataFrame({
    'transaction_id': shared_ids, # This matches the financials ID
    'origin_city': np.random.choice(['London', 'New York', 'Tokyo', 'Berlin', 'Paris'], 1000),
    'weight_kg': np.random.uniform(5.0, 600.0, 1000).round(2),
    'shipping_cost': np.random.uniform(20.0, 1500.0, 1000).round(2)
})

# 5. SAVE FILES (Clean up any old directories first)
for name, df in [("financials", df_fin), ("logistics", df_log)]:
    target_path = os.path.join(data_dir, f"{name}.parquet")
    
    # Remove directory if accidentally created by Spark/Pandas previously
    if os.path.isdir(target_path):
        shutil.rmtree(target_path)
        print(f"🧹 Cleaned up directory: {target_path}")
    
    # Save as fresh file
    df.to_parquet(target_path, index=False, engine='pyarrow')
    print(f"✅ Created {name}.parquet with {len(df)} linked rows.")