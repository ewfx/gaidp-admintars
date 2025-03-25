import requests
import json
import base64
import pandas as pd
from typing import List, Dict, Optional

class FINRAAnalyzer:
    def __init__(self, api_key: str, model: str = "deepseek/deepseek-r1-zero:free"):
        """
        Initialize the FINRA document analyzer with API credentials
        
        Args:
            api_key: Your OpenRouter API key
            model: The model to use (default: deepseek-r1)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
    def _encode_document(self, file_path: str) -> str:
        """
        Encode the document to base64 for API upload
        
        Args:
            file_path: Path to the FINRA document (PDF, DOCX, etc.)
            
        Returns:
            Base64 encoded string of the document
        """
        with open(file_path, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode('utf-8')
        return encoded_string
    
    def _call_openrouter_api(self, messages: List[Dict], files: Optional[List] = None) -> Dict:
        """
        Make a request to the OpenRouter API
        
        Args:
            messages: List of message dictionaries for the chat
            files: Optional list of files to include
            
        Returns:
            API response as a dictionary
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
        }
        
        if files:
            payload["files"] = files
        
        response = requests.post(self.base_url, headers=headers, json=payload)
        print("Deepseek response:", response.json())
        response.raise_for_status()
        return response.json()
    

    def extract_rules(self, document_path: str) -> Dict:
        """
        Extract financial rules from a FINRA document for anomaly detection
        
        Args:
            document_path: Path to the FINRA document
            
        Returns:
            Dictionary containing extracted rules and metadata
        """
        # Encode the document
        # encoded_doc = self._encode_document(document_path)
        
        # Prepare the API request
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a financial compliance expert specializing in FINRA regulations. "
                    "Analyze the provided document and extract all financial rules and requirements "
                    "that could be used for anomaly detection in financial transactions or reporting. "
                    "Pay special attention to numerical thresholds, reporting timelines, "
                    "required procedures, and prohibited activities. "
                    "For tables, extract the data in a structured format."
                )
            },
            {
                "role": "user",
                "content": (
                    "Please analyze this FINRA document and extract all financial rules and requirements "
                    "that could be used to detect anomalies in financial operations. "
                    "Include numerical thresholds, timing requirements, reporting obligations, "
                    "and any other compliance rules. For tables, provide the data in a structured format."
                )
            }
        ]
        
        files = [{
            "name": "finra_document",
            "type": "application/pdf",  # Adjust based on actual file type
            "data": document_path
        }]
        
        # Call the API
        response = self._call_openrouter_api(messages, files)
        
        # Process the response
        try:
            content = response['choices'][0]['message']['content']
            if isinstance(content, str):
                return json.loads(content)
            return content
        except (KeyError, json.JSONDecodeError):
            # If response isn't JSON, return as text
            return {"rules": content}
    
    # def detect_anomalies(self, transaction_data: List[Dict], finra_rules: Dict) -> List[Dict]:
    #     """
    #     Apply extracted FINRA rules to transaction data to detect anomalies using LLM analysis
        
    #     Args:
    #         transaction_data: DataFrame containing financial transactions
    #         finra_rules: Dictionary of rules extracted from FINRA documents
            
    #     Returns:
    #         List of dictionaries with anomaly detection results for each transaction
    #     """
    #     results = []
        
    #     # Convert DataFrame to list of dictionaries for JSON serialization
    #     # transactions = transaction_data.to_dict('records')
        
    #     # Process transactions in batches to avoid overwhelming the API
    #     print("transaction data:", transaction_data)
    #     batch_size = 5  # Adjust based on your API limits
    #     for i in range(0, len(transaction_data), batch_size):
    #         batch = transaction_data[i:i + batch_size]
            
    #         prompt = f"""
    #         You are an AI-powered anomaly detection system analyzing financial transactions against FINRA compliance rules when list of transactions are given.

    #         ### **FINRA Rules:**
    #         {json.dumps(finra_rules, indent=2)}

    #         ### **Transactions to Analyze:**
    #         {json.dumps(batch, indent=2)}

    #         For each transaction, determine if any field violates any FINRA rules. If it does, return:
    #         {{
    #             "transaction_id": "<ID>",
    #             "status": "ANOMALY",
    #             "reason": List["<violation description>"]
    #         }}

    #         If the transaction is normal, return:
    #         {{
    #             "transaction_id": "<ID>",
    #             "status": "NORMAL"
    #         }}

    #         Return only valid JSON output as a list of these objects.
    #         """

    #         payload = {
    #             "model": self.model,
    #             "messages": [
    #                 {"role": "system", "content": "You are a financial anomaly detection AI."},
    #                 {"role": "user", "content": prompt}
    #             ],
    #             "temperature": 0.0
    #         }

    #         try:
    #             response = self._call_openrouter_api(payload['messages'])
    #             output_text = response.json()
    #             print("Anomaly output", output_text)
                
    #             try:
    #                 batch_results = json.loads(output_text)
    #                 if isinstance(batch_results, list):
    #                     results.extend(batch_results)
    #                 else:
    #                     # Handle single result case
    #                     results.append(batch_results)
    #             except json.JSONDecodeError:
    #                 print(f"Warning: Could not parse LLM response for batch {i//batch_size}")
    #                 # Mark all transactions in this batch as errored
    #                 for tx in batch:
    #                     results.append({
    #                         "transaction_id": tx.get('id', 'unknown'),
    #                         "status": "ERROR",
    #                         "reason": ["Could not parse analysis result"]
    #                     })
                        
    #         except Exception as e:
    #             print(f"Error processing batch {i//batch_size}: {str(e)}")
    #             # Mark all transactions in this batch as errored
    #             for tx in batch:
    #                 results.append({
    #                     "transaction_id": tx.get('id', 'unknown'),
    #                     "status": "ERROR",
    #                     "reason": [f"Analysis failed: {str(e)}"]
    #                 })
    
    #     # Merge results back with original transaction data
    #     if 'id' in transaction_data.columns:
    #         result_df = transaction_data.copy()
    #         result_df['analysis_result'] = results
    #         return result_df
    #     else:
    #         # If no ID column, just return the results list
    #         return results

    def detect_anomalies(self, transactions: List[Dict], finra_rules: Dict) -> List[Dict]:
        """
        Detect anomalies in financial transactions against FINRA rules
        
        Args:
            transactions: List of transaction dictionaries
            finra_rules: Dictionary of rules extracted from FINRA documents
            
        Returns:
            List of anomaly detection results
        """
        # Prepare the prompt
        prompt = f"""
        Analyze these financial transactions against FINRA compliance rules and identify any anomalies.

        FINRA Rules:
        {json.dumps(finra_rules, indent=2)}

        Transactions:
        {json.dumps(transactions, indent=2)}

        For each transaction, return:
        - "transaction_id": The original transaction ID
        - "status": "NORMAL" or "ANOMALY"
        - "reasons": [List of reasons if anomaly] (optional)

        Return only valid JSON in this format:
        {{
            "results": [
                {{
                    "transaction_id": "tx123",
                    "status": "ANOMALY",
                    "reasons": ["Amount exceeds $10,000 reporting threshold"]
                }},
                {{
                    "transaction_id": "tx124",
                    "status": "NORMAL"
                }}
            ]
        }}
        """
        
        messages = [
            {
                "role": "system",
                "content": "You are a financial compliance AI that detects anomalies in transactions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            # Call the API
            response = self._call_openrouter_api(messages)
            
            # Get the content from the response
            content = response['choices'][0]['message']['content']
            
            # Parse the JSON content
            if isinstance(content, str):
                result = json.loads(content)
            else:
                result = content
            
            # Validate and normalize the response format
            if "results" in result:
                return result["results"]
            elif isinstance(result, list):
                return result
            else:
                raise ValueError("Unexpected response format from API")
                
        except Exception as e:
            # Return error status for all transactions if analysis fails
            error_message = f"Anomaly detection failed: {str(e)}"
            return [
                {
                    "transaction_id": tx.get("transaction_id", "unknown"),
                    "status": "ERROR",
                    "reasons": [error_message]
                }
                for tx in transactions
            ]


# Example usage
if __name__ == "__main__":
    # Initialize the analyzer with your API key
    api_key = "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"
    analyzer = FINRAAnalyzer(api_key)
    
    # Path to your FINRA document
    rule_document_path = "../../../artifacts/arch/rules2.pdf"
    transaction_path = "transactions.json"
    # Extract rules from the document
    rules = analyzer.extract_rules(rule_document_path)
    print("Extracted Rules:")
    print(json.dumps(rules, indent=2))
    
    # Example transaction data (in practice, you'd load your real data)
    with open("../ExtractPdf/transactions.json", "r") as file:
        example_data = json.load(file)

    example_document = example_data.get("corporate_loans", [])
    # example_data = pd.DataFrame({
    #     'transaction_amount': [5000, -1000, 25000, 500, 100000],
    #     'client_id': ['A123', 'B456', 'A123', 'C789', 'D012'],
    #     'transaction_date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
    # })
    
    # Detect anomalies
    analyzed_data = analyzer.detect_anomalies(example_document, rules)
    print("\nAnomaly Analysis Results:")
    print(analyzed_data)