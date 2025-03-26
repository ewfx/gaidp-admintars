from typing import Dict, List
import pandas as pd
import numpy as np

class RiskEngine:
    def __init__(self):
        self.risk_rules = [
            {
                'condition': "(transaction['Amount'] > 5000) and (transaction['Country'] in high_risk_countries)",
                'score': 0.8,
                'reason': "High-value transaction in high-risk country"
            },
            {
                'condition': "transaction['Amount'] % 1000 == 0",
                'score': 0.6,
                'reason': "Round-number transaction amount"
            },
            {
                'condition': "transaction['anomaly_score'] == -1",
                'score': 0.7,
                'reason': "Statistical anomaly detected"
            }
        ]
        self.high_risk_countries = ['DE', 'US', 'UK']  # Example list
    
    def calculate_risk_scores(self, transactions: pd.DataFrame) -> pd.DataFrame:
        transactions['risk_score'] = 0.0
        transactions['risk_reasons'] = ""
        
        for _, transaction in transactions.iterrows():
            score = 0.0
            reasons = []
            
            for rule in self.risk_rules:
                try:
                    if eval(rule['condition'], {
                        'transaction': transaction,
                        'high_risk_countries': self.high_risk_countries
                    }):
                        score = max(score, rule['score'])
                        reasons.append(rule['reason'])
                except:
                    continue
            
            # Ensure score is a valid number
            if not np.isfinite(score):
                score = 0.0
            
            transactions.at[transaction.name, 'risk_score'] = score
            transactions.at[transaction.name, 'risk_reasons'] = "; ".join(reasons) or "No risk factors detected"
        
        return transactions