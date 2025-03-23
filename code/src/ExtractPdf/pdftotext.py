import requests
import pdfplumber
import tiktoken
from pdfminer.high_level import extract_text
import pandas as pd
import json

# API Details
API_KEY = "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"
DEEPSEEK_URL = "https://openrouter.ai/api/v1/completions"

# Prompt Template
PROMPT_TEMPLATE = """
You are an expert research assistant. Use the provided context to answer the query. 
If unsure, state that you don't know. Be concise and factual (max 3 sentences).

Query: {user_query} 
Context: 
{document_context} 

Tables: 
{document_tables}

Answer:
"""

# Step 1: Extract Text & Tables from PDF
def extract_text_and_tables(pdf_path):
    print("Extracting text and tables...")

    # Extract text using PDFMiner
    text = extract_text(pdf_path).strip()

    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages[:10]):  # Limit to 10 pages for efficiency
            print(f"Processing tables from page {page_num + 1}...")

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
                df = df.map(lambda x: str(x).strip() if pd.notna(x) else "")

                # Convert DataFrame to Markdown Table Format
                markdown_table = df.to_markdown(index=False)
                all_tables.append(f"\n**Table from Page {page_num+1}:**\n{markdown_table}")

    # Convert tables to a single string
    tables_text = "\n\n".join(all_tables) if all_tables else "No relevant tables found."
    
    return text, tables_text

# Step 2: Sentence-Aware & Token-Based Chunking
def split_into_sentences(text):
    """Splits text into sentences while preserving structure like bullet points and headings."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)  # Split at sentence boundaries
    return [s.strip() for s in sentences if s.strip()]  # Remove empty elements

def dynamic_chunking(text, max_tokens=2048, overlap=300):
    """
    Splits text into structured chunks using sentence-based and token-aware splitting.
    This prevents cutting off sentences mid-way while ensuring compliance with model token limits.
    """
    enc = tiktoken.get_encoding("cl100k_base")  # Use DeepSeek-compatible tokenizer
    sentences = split_into_sentences(text)  # Split text into sentences first

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        token_count = len(enc.encode(sentence))  # Get token count for the sentence

        if current_length + token_count > max_tokens:  # If chunk is too big, start new one
            chunks.append(enc.decode(enc.encode(" ".join(current_chunk))))  # Convert back to text
            current_chunk = current_chunk[-overlap:]  # Keep overlap
            current_length = sum(len(enc.encode(s)) for s in current_chunk)

        current_chunk.append(sentence)
        current_length += token_count

    # Add the last chunk
    if current_chunk:
        chunks.append(enc.decode(enc.encode(" ".join(current_chunk))))

    return chunks

# Step 3: Send Processed Text to DeepSeek-R1
def send_to_deepseek(user_query, document_chunks, document_tables):
    document_context = "\n\n".join(document_chunks[:3])  # Use top 3 chunks to stay within token limits
    formatted_prompt = PROMPT_TEMPLATE.format(user_query=user_query, document_context=document_context, document_tables=document_tables)

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
user_query = "Extract the rules from this document in a form which can be used to verify against a transactional dataset of a user"

# Processing
extracted_text, extracted_tables = extract_text_and_tables(pdf_path)
document_chunks = dynamic_chunking(extracted_text, max_tokens=2048, overlap=300)

if document_chunks:
    deepseek_response = send_to_deepseek(user_query, document_chunks, extracted_tables)
    print("Extracted Answer:\n", deepseek_response)
else:
    print("Failed to extract text from PDF.")
