import PyPDF2
import requests
import json
import base64
import pandas as pd
from typing import List, Dict, Optional
from io import StringIO
import re

class FINRAAnalyzer:
    def __init__(self, api_key: str, model: str = "cognitivecomputations/dolphin3.0-r1-mistral-24b:free"):
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
        # print("Deepseek response:", response.json())
        response.raise_for_status()
        return response.json()
    
    def extract_text_from_pdf(self, pdf_path: str):
        """
        Extracts text from a PDF, including text in tables (as best as possible)
        """
        text = ""
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page in reader.pages:
                # Extract normal text
                page_text = page.extract_text()
                
                # Try to extract table-like content by looking for patterns
                # This is a simple approach - for complex tables consider camelot or pdfplumber
                if page_text:
                    # Clean up the text
                    page_text = re.sub(r'\s+', ' ', page_text).strip()
                    text += page_text + "\n\n"
                    
        return text

    def chunk_text(self, text, max_chunk_size=3000):
        """
        Split text into chunks that fit within the context window,
        trying to preserve paragraphs and logical sections
        """
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 < max_chunk_size:  # +2 for the newlines
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = para + "\n\n"
                else:
                    # This paragraph is too long, split it arbitrarily
                    chunks.append(para[:max_chunk_size])
                    remaining = para[max_chunk_size:]
                    if remaining:
                        chunks.append(remaining)
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

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
        system_prompt = """You are a financial analyst expert. Your task is to extract and summarize key financial rules, 
            regulations, policies, and important financial information from the provided text. 

            Instructions:
            1. Focus on extracting rules, policies, thresholds, limits, requirements, and compliance information.
            2. Organize the information in a clear, structured manner.
            3. Maintain context between different sections of the document.
            4. For each rule, include the relevant context that explains its purpose or application.
            5. If you encounter numerical values, percentages, or financial thresholds, pay special attention to them.
            6. Output should be in Markdown format with clear headings and bullet points.
            
            Current extraction will be done in chunks. I'll provide you with the previous summary after each chunk to maintain continuity."""

        text = self.extract_text_from_pdf(document_path)
        text_chunks = self.chunk_text(text)

        full_summary = ""
        previous_context = ""

        for i, chunk in enumerate(text_chunks):
            print(f"Processing chunk {i+1}/{len(text_chunks)}...")
            
            user_prompt = f"""
            Here is chunk {i+1} of the document:
            {chunk}
            
            {f'Here is the summary from previous chunks for context:\n{previous_context}' if previous_context else 'This is the first chunk of the document.'}
            
            Please extract any new financial rules or information from this chunk, integrating it with the previous context if available.
            """
            
            messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]

            try: 
        # Call the API
                response = self._call_openrouter_api(messages)
                print("#"*50)
                print(response)
                chunk_summary = response['choices'][0]['message']['content']
                full_summary += f"\n\n## Chunk {i+1} Results\n\n{chunk_summary}"
                previous_context = chunk_summary
            except Exception as e:
                print(f"Error processing chunk {i+1}: {str(e)}")
                continue
        # Process the response
        consolidation_prompt = f"""
            Here is the complete extracted financial information from all chunks:
            {full_summary}
            
            Please consolidate this into a final, well-organized set of financial rules and policies:
            - Remove any duplicates
            - Organize by topic/category
            - Ensure consistent formatting
            - Add headings and subheadings as needed
            - Include any important context for each rule
            """
        
        messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": consolidation_prompt}
            ]
        
        try:
            response = self._call_openrouter_api(messages)
            final_result = response.json()['choices'][0]['message']['content']
            return final_result
        except Exception as e:
            print(f"Error during final consolidation: {str(e)}")
            return full_summary

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
            response = self._call_openrouter_api(messages)
            result = response
            output_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            try:
                return output_text  # Ensure the output is valid JSON
            except json.JSONDecodeError:
                return {"error": "Invalid response from LLM"}
        except requests.RequestException as e:
            print(f"Error: API request failed - {e}")
            return {"error": "API request failed"}


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