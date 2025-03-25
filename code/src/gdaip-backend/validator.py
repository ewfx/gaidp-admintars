import pandas as pd
import uuid
import re
import random
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import IsolationForest

class DataValidator:
    def __init__(self):
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

    def validate_transactions(self, data: pd.DataFrame, rules: List[Dict]) -> Tuple[pd.DataFrame, List[Dict]]:
        """Generalized validation for any regulatory data"""
        # Ensure we have a transaction identifier
        data = self._ensure_transaction_id(data)
        print("In validator.py")
        
        # Apply rule-based validation
        validation_results = []
        for _, row in data.iterrows():
            result = self._validate_row(row, rules)
            validation_results.append(result)
        
        # Apply statistical anomaly detection
        data = self._detect_anomalies(data, validation_results)
        
        # Generate risk assessment
        risk_assessment = self._assess_risk(data, validation_results)
        
        # Generate remediation actions
        remediations = [self._generate_remediation(r) for r in validation_results]
        
        return {
            "validation_results": validation_results,
            "risk_assessment": risk_assessment.to_dict('records'),
            "remediation_actions": remediations
        }

    def _ensure_transaction_id(self, data: pd.DataFrame) -> pd.DataFrame:
        """Ensure each record has a unique transaction ID"""
        if 'transaction_id' not in data.columns:
            if 'Customer_ID' in data.columns:
                data['transaction_id'] = data['Customer_ID'].astype(str)
            else:
                data['transaction_id'] = [str(uuid.uuid4())[:8] for _ in range(len(data))]
        return data

    def _validate_row(self, row: pd.Series, rules: List[Dict]) -> Dict:
        """Validate a single row against all rules"""
        result = {
            "transaction_id": row['transaction_id'],
            "fields_checked": [],
            "violations": [],
            "anomaly_score": None
        }
        
        for rule in rules:
            try:
                field_errors = self._apply_rule(row, rule)
                if field_errors:
                    result["violations"].extend(field_errors)
                result["fields_checked"].extend(rule.get('fields', []))
            except Exception as e:
                result["violations"].append(f"Rule processing error: {str(e)}")
        
        return result

    def _apply_rule(self, row: pd.Series, rule: Dict) -> List[str]:
        """Apply a single validation rule to a row"""
        errors = []
        for field in rule.get('fields', []):
            if field not in row:
                errors.append(f"Missing required field: {field}")
                continue
                
            value = row[field]
            
            # Apply built-in common validations
            if 'validation_logic' not in rule:
                if isinstance(value, str) and not self.common_validation_rules['string_not_empty'](value):
                    errors.append(f"Invalid {field}: must be non-empty string")
                elif isinstance(value, (int, float)) and not self.common_validation_rules['valid_number'](value):
                    errors.append(f"Invalid {field}: must be valid number")
                continue
                
            # Apply custom validation logic
            try:
                valid = eval(rule['validation_logic'], {}, {'row': row, 'value': value})
                if not valid:
                    errors.append(rule.get('description', f"Validation failed for {field}"))
            except Exception as e:
                errors.append(f"Validation error for {field}: {str(e)}")
        
        return errors

    def _detect_anomalies(self, data: pd.DataFrame, validation_results: List[Dict]) -> pd.DataFrame:
        """Apply statistical anomaly detection"""
        # Convert validation results to anomaly scores
        for i, result in enumerate(validation_results):
            result['anomaly_score'] = 1 if result['violations'] else -1
        
        # Additional statistical anomaly detection
        numeric_cols = data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            try:
                anomalies = self.anomaly_detector.fit_predict(data[numeric_cols])
                for i, score in enumerate(anomalies):
                    if score == -1 and validation_results[i]['anomaly_score'] != 1:
                        validation_results[i]['anomaly_score'] = 0.5  # Potential anomaly
                        validation_results[i]['violations'].append("Statistical anomaly detected")
            except Exception:
                pass  # Skip if anomaly detection fails
                
        return data

    def _assess_risk(self, data: pd.DataFrame, validation_results: List[Dict]) -> pd.DataFrame:
        """Calculate risk scores based on validation results"""
        risk_scores = []
        risk_reasons = []
        
        for result in validation_results:
            # Base risk score on number and severity of violations
            score = min(1.0, len(result['violations']) * 0.2 + random.uniform(0, 0.1))
            
            reasons = []
            if result['violations']:
                reasons.append(f"{len(result['violations'])} validation issues")
            if result['anomaly_score'] > 0:
                reasons.append("Anomalous patterns detected")
                
            risk_scores.append(score)
            risk_reasons.append("; ".join(reasons) if reasons else "Low risk")
        
        data['risk_score'] = risk_scores
        data['risk_reasons'] = risk_reasons
        return data

    def _generate_remediation(self, result: Dict) -> Dict:
        """Generate remediation actions for validation results"""
        actions = set()
        doc_required = False
        
        for violation in result['violations']:
            # Generic remediation based on violation type
            if "missing" in violation.lower():
                actions.add("Provide missing field data")
                doc_required = True
            elif "invalid" in violation.lower():
                field = violation.split(':')[0].replace("Invalid", "").strip()
                actions.add(f"Correct {field} value")
                doc_required = True
            elif "anomaly" in violation.lower():
                actions.add("Review for potential data issues")
                doc_required = True
        
        return {
            "transaction_id": result["transaction_id"],
            "issues": result["violations"],
            "actions": list(actions) or ["No action required"],
            "documentation_required": doc_required
        }