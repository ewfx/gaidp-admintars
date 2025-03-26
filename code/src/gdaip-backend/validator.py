import pandas as pd
import uuid
import re
import random
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import IsolationForest
import numpy as np
from deepseek_adapter import DeepSeekAdapter
import json

class DataValidator:
    def __init__(self, api_key: str = None):
        self.llm_adapter = DeepSeekAdapter(api_key) if api_key else None
        self.anomaly_detector = IsolationForest(contamination=0.1)
        self.common_validation_rules = {
            'string_not_empty': lambda x: isinstance(x, str) and len(x.strip()) > 0,
            'valid_number': lambda x: isinstance(x, (int, float)) and not pd.isna(x),
            'non_negative': lambda x: x >= 0,
            'date_format_YYYYMM': lambda x: (isinstance(x, str) and 
                                           len(x) == 6 and 
                                           x.isdigit() and
                                           1 <= int(x[4:6]) <= 12)
        }

    async def validate_transactions(self, data: List[Dict], rules: List[Dict]) -> Dict:
        """
        New LLM-powered validation that maintains the same return structure
        """
        prompt = self._build_validation_prompt(data, rules)
        
        try:
            llm_response = self.llm_adapter.generate(prompt, max_tokens=3000, temperature=0.1)
            return self._parse_llm_response(llm_response)
        except Exception as e:
            return self._fallback_validation(data, rules)

    def _build_validation_prompt(self, data: List[Dict], rules: List[Dict]) -> str:
        return f"""
        Perform financial data validation with these requirements:
        
        1. Use EXACTLY this JSON structure:
        {{
            "validation_results": [
                {{
                    "transaction_id": "id",
                    "violations": ["rule1", "rule2"],
                    "risk_score": 0.0-1.0
                }}
            ],
            "risk_assessment": [
                {{
                    "transaction_id": "id",
                    "risk_score": 0.0-1.0,
                    "risk_reasons": ["reason1"]
                }}
            ],
            "remediation_actions": [
                {{
                    "transaction_id": "id",
                    "actions": ["action1"],
                    "documentation_required": true/false
                }}
            ]
        }}
        
        2. Apply these rules to the data:
        Rules: {json.dumps(rules, indent=2)}
        
        3. Validate this data:
        Data: {json.dumps(data, indent=2)}
        
        4. Important:
        - Maintain the exact JSON structure above
        - Include ALL transaction IDs from input
        - Ensure violations are being mapped to the correct transaction ID.
        - Specify what it was expecting and what it got. If not expecting anything, specify that.
        - risk_score must be 0.0-1.0
        - Never add comments or text outside JSON
        """

    def _parse_llm_response(self, response: str) -> Dict:
        try:
            # Extract JSON from markdown code blocks if present
            json_str = response.split('```json')[1].split('```')[0] if '```json' in response else response
            return json.loads(json_str)
        except:
            raise ValueError("Failed to parse LLM response")

    def _fallback_validation(self, data: List[Dict], rules: List[Dict]) -> Dict:
        """Fallback to simple validation if LLM fails"""
        return {
            "validation_results": [{
                "transaction_id": str(d.get('transaction_id', idx)),
                "violations": [],
                "risk_score": 0.0
            } for idx, d in enumerate(data)],
            "risk_assessment": [],
            "remediation_actions": []
        }