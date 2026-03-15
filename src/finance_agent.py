import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class FinanceAgent:
    def __init__(self):
        pass

    def analyze_financial_data(self, file_path: str):
        """Analyzes a CSV file to find statistical anomalies."""
        try:
            df = pd.read_csv(file_path)
            mean = df['Amount'].mean()
            std = df['Amount'].std()
            threshold = mean + (3 * std)
            anomalies = df[df['Amount'] > threshold]
            return f"Found {len(anomalies)} anomalies. Threshold was {threshold:.2f}"
        except Exception as e:
            return f"Error: {e}"

    def predict_future_spending(self, file_path: str):
        """Predicts total spending for the next month."""
        try:
            df = pd.read_csv(file_path)
            total = df['Amount'].sum()
            prediction = total * 1.05 # Simple 5% growth forecast
            return f"Predicted next month spending: ${prediction:.2f}"
        except Exception as e:
            return f"Error: {e}"

    # --- THIS IS THE MISSING PIECE ---
    def create_anomaly_chart(self, file_path: str):
        """Creates a chart of anomalies and saves it as anomalies_chart.png."""
        try:
            df = pd.read_csv(file_path)
            mean = df['Amount'].mean()
            std = df['Amount'].std()
            threshold = mean + (3 * std)
            
            plt.figure(figsize=(10, 6))
            plt.scatter(df.index, df['Amount'], c=(df['Amount'] > threshold), cmap='coolwarm')
            plt.axhline(y=threshold, color='r', linestyle='--', label='Threshold')
            plt.title("Financial Anomalies")
            plt.savefig("anomalies_chart.png")
            plt.close()
            return "Chart saved successfully as anomalies_chart.png"
        except Exception as e:
            return f"Error creating chart: {e}"