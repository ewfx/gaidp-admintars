import requests
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd
import json

# API Details
API_KEY = "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"
DEEPSEEK_URL = "https://openrouter.ai/api/v1/completions"

# Prompt Template Extracted from Your Code
PROMPT_TEMPLATE = """
You are an expert research assistant. Use the provided context to answer the query. 
If unsure, state that you don't know. Be concise and factual (max 3 sentences).

Query: {user_query} 
Context: {document_context} 
Answer:
"""

# Step 1: Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    print("Extracting text and tables...")
    text = ""
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages[:10]):  # Limit to 10 pages
            print(f"Processing page {page_num + 1}...")
            
            # Extract text
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue  # Skip empty tables
                
                # Convert to DataFrame & clean
                df = pd.DataFrame(table)

                # Remove empty rows & columns
                df.dropna(how='all', axis=0, inplace=True)
                df.dropna(how='all', axis=1, inplace=True)

                if df.empty:
                    continue  # Skip if no meaningful data

                # Ensure headers are valid
                df.columns = [str(col).strip() if col else f"Column_{i}" for i, col in enumerate(df.iloc[0])]
                df = df[1:].reset_index(drop=True)  # Remove first row (now used as header)

                # Convert all values to strings & strip whitespace
                df = df.applymap(lambda x: str(x).strip() if pd.notna(x) else "")

                # Convert DataFrame to list of dicts
                all_tables.append(df.to_dict(orient="records"))
        # Convert to JSON
    json_output = json.dumps(all_tables, indent=4, ensure_ascii=False)

    return text.strip(), json_output

# Step 2: Chunk the Extracted Text
def chunk_documents(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_text(text)

# Step 3: Send Processed Text to DeepSeek-R1
def send_to_deepseek(user_query, document_chunks):
    document_context = "\n\n".join(document_chunks[:5])  # Limit context to first 5 chunks
    formatted_prompt = PROMPT_TEMPLATE.format(user_query=user_query, document_context=document_context)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek/deepseek-r1-zero:free",
        "prompt": formatted_prompt,
        "max_tokens": 1024
    }

    response = requests.post(DEEPSEEK_URL, headers=headers, json=payload)
    return response.json().get("choices", [{}])[0].get("text", "").strip() if response.status_code == 200 else f"Error: {response.json()}"

# Example Usage
pdf_path = "../../../artifacts/arch/rules.pdf"  # Replace with actual PDF file path
user_query = "What are the financial compliance rules from this FINRA document?"

# Processing
extracted_text = extract_text_from_pdf(pdf_path)
# document_chunks = chunk_documents(extracted_text)

if extracted_text:
    deepseek_response = send_to_deepseek(user_query, extracted_text)
    print("Extracted Answer:\n", deepseek_response)
else:
    print("Failed to extract text from PDF.")
