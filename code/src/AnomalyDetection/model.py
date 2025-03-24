import json
import requests

# OpenRouter API Key (Store this securely)
API_KEY = "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"

# OpenRouter API URL for Dolphin 3.0 R1
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Load FINRA rules from JSON file
with open("../ExtractPdf/rules.json", "r") as file:
    finra_rules = json.load(file)

# Load transactional data
with open("../ExtractPdf/transactions.json", "r") as file:
    transactions_data = json.load(file)

transactions = transactions_data.get("corporate_loans", [])

BATCH_SIZE = 10  

def process_batch(batch):
    prompt = f"""
    You are an AI-powered anomaly detection system analyzing financial transactions against FINRA compliance rules.

    ### **FINRA Rules:**
    {json.dumps(finra_rules, indent=2)}

    ### **Transactions to Analyze:**
    {json.dumps(batch, indent=2)}

    For each transaction, determine if any field violates any FINRA rules. If it does, return:
    {{
        "transaction_id": "<ID>",
        "status": "ANOMALY",
        "reason": List["<violation description>"]
    }}

    If the transaction is normal, return:
    {{
        "transaction_id": "<ID>",
        "status": "NORMAL"
    }}

    Return only valid JSON output.
    """

    payload = {
        "model": "cognitivecomputations/dolphin3.0-r1-mistral-24b:free",
        "messages": [{"role": "system", "content": "You are a financial anomaly detection AI."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.0
    }

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for HTTP issues
        result = response.json()
        output_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        try:
            return json.loads(output_text)  # Ensure the output is valid JSON
        except json.JSONDecodeError:
            print("Error: Invalid JSON response from API")
            return {"error": "Invalid response from LLM"}
    except requests.RequestException as e:
        print(f"Error: API request failed - {e}")
        return {"error": "API request failed"}

# Process transactions in batches
all_anomalies = []
for i in range(0, len(transactions), BATCH_SIZE):
    batch = transactions[i:i + BATCH_SIZE]
    print(f"Processing batch {i // BATCH_SIZE + 1}: {batch}")  # Debugging log
    anomalies = process_batch(batch)
    print("API response:", anomalies)  # Debugging log
    if isinstance(anomalies, list):
        all_anomalies.extend(anomalies)
    else:
        print(f"Error: Unexpected response format for batch {i // BATCH_SIZE + 1}")

# Save anomalies to a JSON file
with open("anomalies.json", "w") as file:
    json.dump(all_anomalies, file, indent=4)

print(f"Processed {len(transactions)} transactions. Anomalies saved to anomalies.json!")