import pandas as pd
import numpy as np
import os

def create_synthetic_data(rows=1000):
    np.random.seed(42) # Ensures you get the same "random" data every time
    
    data = {
        'Transaction_ID': [f'TX{i}' for i in range(rows)],
        'Amount': np.random.normal(100, 50, rows).clip(10, 500), # Normal transactions
        'Frequency': np.random.randint(1, 20, rows),
        'Age_of_Account': np.random.randint(1, 120, rows), # in months
        'Type': np.random.choice(['Transfer', 'Withdrawal', 'Payment'], rows),
        'Is_Anomalous': 0 # We will hide some anomalies below
    }
    
    df = pd.DataFrame(data)
    
    # 2. Inject 2% "Manual" Anomalies (The needles in the haystack)
    anomaly_idx = np.random.choice(df.index, size=int(rows * 0.02), replace=False)
    df.loc[anomaly_idx, 'Amount'] = df.loc[anomaly_idx, 'Amount'] * 15 # Huge spike
    df.loc[anomaly_idx, 'Is_Anomalous'] = 1
    
    # Save it to your /data folder
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/financial_data.csv', index=False)
    print(f"Successfully generated {rows} rows in 'data/financial_data.csv'")

if __name__ == "__main__":
    create_synthetic_data()