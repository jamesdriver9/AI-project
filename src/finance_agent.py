import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from langchain.tools import tool

class FinanceAgent:
    def __init__(self):
        self.encoder = LabelEncoder()

    @tool
    @staticmethod
    def analyze_financial_data(file_path: str):
        """Useful for when you need to load a CSV and find statistical anomalies or outliers."""
        df = pd.read_csv(file_path)
        mean_val = df['Amount'].mean()
        std_val = df['Amount'].std()
        threshold = mean_val + (3 * std_val)
        anomalies = df[df['Amount'] > threshold]
        
        return {
            "total_records": len(df),
            "anomalies_found": len(anomalies),
            "suggested_risk_threshold": round(threshold, 2)
        }

    @tool
    def predict_future_spending(self, file_path: str):
        """Useful for when you want to forecast or project total spending for the next period."""
        df = pd.read_csv(file_path)
        
        # Simple Logic: Get the average spending and add a 5% 'inflation/growth' buffer
        current_total = df['Amount'].sum()
        projected_total = current_total * 1.05 
        
        return {
            "current_total": round(current_total, 2),
            "projected_next_month": round(projected_total, 2),
            "growth_rate_assumed": "5%"
        }

finance_logic = FinanceAgent()
tools = [finance_logic.analyze_financial_data, finance_logic.predict_future_spending]