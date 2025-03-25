import os
import requests
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd
import json
import tiktoken
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# API Details
API_KEY = "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"
DEEPSEEK_URL = "https://openrouter.ai/api/v1/completions"

# Prompt Template
PROMPT_TEMPLATE = """
You are an expert research assistant. Use the provided context to answer the query. 
If unsure, state that you don't know. Be concise and factual (max 3 sentences).

Query: {user_query} 
Context: {document_context} 
Answer:
"""

# Step 1: Extract Text from PDF
def extract_text_from_pdf(pdf_path, max_pages=50):
    print("Extracting text and tables...")
    text = ""
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages[:25]  # Limit to max_pages

        # Parallel extraction of text and tables
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(extract_text_and_tables_from_page, pages))

        for page_text, page_tables in results:
            if page_text:
                text += page_text + "\n"
            all_tables.extend(page_tables)

    tables_text = "\n\n".join(all_tables) if all_tables else "No relevant tables found."
    # Combine extracted text and tables
    combined_text = text.strip() + "\n\n" + tables_text
    return combined_text

def extract_text_and_tables_from_page(page):
    page_text = page.extract_text()
    tables = page.extract_tables()
    page_tables = []

    for table in tables:
        if not table:
            continue  # Skip empty tables
        
        # Convert to DataFrame & clean
        df = pd.DataFrame(table)
        df.dropna(how='all', axis=0, inplace=True)
        df.dropna(how='all', axis=1, inplace=True)

        if df.empty:
            continue  # Skip if no meaningful data

        # Convert DataFrame to a compact format (CSV-like, no Markdown formatting)
        table_text = df.to_csv(index=False, sep="|").replace("\n", " ; ")
        page_tables.append(f"\n**Table from Page {page.page_number}:**\n{table_text}")

    return page_text, page_tables

# Step 2: Chunk the Extracted Text
def chunk_documents(text, chunk_size=2000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_text(text)

# Step 3: Prepare and Send Chunks to DeepSeek-R1
async def prepare_and_send_chunks(user_query, document_chunks, max_tokens=16000, max_context_chunks=80):
    enc = tiktoken.get_encoding("cl100k_base")
    document_context = "\n\n".join(document_chunks)  # Limit context to first max_context_chunks

    # Calculate total characters and tokens
    total_characters = sum(len(chunk) for chunk in document_chunks[:max_context_chunks])
    total_tokens = sum(len(enc.encode(chunk)) for chunk in document_chunks[:max_context_chunks])

    print(f"Total Characters in Chunks: {total_characters}")
    print(f"Total Tokens in Chunks: {total_tokens}")

    formatted_prompt = PROMPT_TEMPLATE.format(user_query=user_query, document_context=document_context)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek/deepseek-r1-zero:free",
        "prompt": formatted_prompt,
        "max_tokens": max_tokens
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(DEEPSEEK_URL, headers=headers, json=payload) as response:
            try:
                response_json = await response.json()
                if response.status == 200:
                    return response_json.get("choices", [{}])[0].get("text", "").strip()
                else:
                    return f"Error: {response_json.get('error', await response.text())}"
            except aiohttp.ClientResponseError:
                return f"Error: Unable to parse API response: {await response.text()}"

# Example Usage
async def main():
    pdf_path = "C:/Users/SHARON JAIN/OneDrive/Desktop/Hackathon/gaidp-admintars/artifacts/arch/rules_new.pdf"

    user_query = f"""  You are an AI trained in data validation. Below is extracted text from a financial document. Identify all schema validation rules relevant to a dataset. 
    These rules should define constraints like column names, data types, formats, and permissible values.
    
    If any tables are present, consider them as structured data and infer rules from them.


    Output the rules in a structured JSON format:

    {{
      "rules": [
        {{
          "column_name": "<name>",
          "data_type": "<type>",
          "constraints": "<e.g., not null, must be unique>",
          "allowed_values": "<if applicable>",
          "references": "<document section or page>"
        }}
      ]
    }}
    """


    # Step 1: Extract text & tables
    extracted_text = extract_text_from_pdf(pdf_path)

    # Step 2: Check for extracted text
    if not extracted_text.strip():
        print("No text extracted from PDF. Please check the document format.")
        return

    # Step 3: Chunk text
    document_chunks = chunk_documents(extracted_text)

    # Step 4: Send query to DeepSeek-R1
    if document_chunks:
        deepseek_response = await prepare_and_send_chunks(user_query, document_chunks)
        print("Extracted Answer:\n", deepseek_response)
    else:
        print("No meaningful text chunks generated.")

if __name__ == "__main__":
    asyncio.run(main())