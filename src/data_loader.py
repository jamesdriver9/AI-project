import pandas as pd
import os

def load_financial_data(filename):
    # 1. Get the absolute path of the folder THIS script is in (AI-project/src)
    current_folder = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Go up one level to the Project Root (AI-project)
    project_root = os.path.dirname(current_folder)
    
    # 3. Create the full path to the data file
    data_path = os.path.join(project_root, 'data', filename)
    
    print(f"DEBUG: Looking for file at: {data_path}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Missing file! Make sure {filename} is inside the 'data' folder.")
    
    return pd.read_csv(data_path)
