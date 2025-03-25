from typing import Dict, List

class RemediationEngine:
    def generate_remediation_actions(self, violations: List[Dict]) -> List[Dict]:
        """Generate remediation actions for validation violations"""
        actions = []
        
        for violation in violations:
            action = {
                'transaction_id': violation.get('transaction_id', ''),
                'issues': violation.get('violations', []),
                'actions': [],
                'documentation_required': False
            }
            
            if any("Amount" in v for v in violation['violations']):
                action['actions'].append("Verify amount with source documentation")
                action['documentation_required'] = True
                
            if any("Balance" in v for v in violation['violations']):
                action['actions'].append("Check account type for overdraft authorization")
                
            if violation.get('anomaly_score', 0) < 0:
                action['actions'].append("Review for potential suspicious activity")
                action['documentation_required'] = True
                
            if not action['actions']:
                action['actions'].append("No specific action required - review recommended")
                
            actions.append(action)
        
        return actions