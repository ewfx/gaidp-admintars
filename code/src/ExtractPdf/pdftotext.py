import requests
import pdfplumber
import tiktoken
import pandas as pd
import json
import re
import concurrent.futures
from pdfminer.high_level import extract_text

# API Details
API_KEY = "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"
DEEPSEEK_URL = "https://openrouter.ai/api/v1/completions"

# ✅ Updated Prompt Template (Includes Tables)
# ✅ Updated Prompt Template (Includes Tables)
PROMPT_TEMPLATE = """
You are a financial compliance expert analyzing a regulatory document.
This is part {chunk_number} of {total_chunks} from a larger document.

Use the provided context to extract key financial compliance rules.
If rules refer to tables, reference them correctly. If context is incomplete, state it clearly.

Query: Extract the rules from this document in a form which can be used to verify against a transactional dataset of a user.

Context (Part {chunk_number} of {total_chunks}): 
{document_context}

Tables Extracted from Document:
{document_tables}

Summary of Previous Chunks (if available): 
{previous_summaries}

Extracted Compliance Rules:
"""

# ✅ Step 1: Extract Text & Tables from PDF
def extract_text_and_tables(pdf_path, max_table_rows=5):
    """Extracts text using PDFMiner and tables using pdfplumber, while limiting table size."""
    print("Extracting text and tables...")

    # Extract text using PDFMiner
    text = extract_text(pdf_path).strip()

    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"Processing tables from page {page_num + 1}...")

            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue  

                # Convert to DataFrame & clean
                df = pd.DataFrame(table)
                df.dropna(how='all', axis=0, inplace=True)
                df.dropna(how='all', axis=1, inplace=True)

                if df.empty:
                    continue  

                # If table has more than max_table_rows, keep first & last 5 rows only
                if len(df) > max_table_rows * 2:
                    df = pd.concat([df.head(max_table_rows), df.tail(max_table_rows)])

                # Convert DataFrame to a compact format (CSV-like, no Markdown formatting)
                table_text = df.to_csv(index=False, sep="|").replace("\n", " ; ")
                all_tables.append(f"\n**Table from Page {page_num+1} (Trimmed to {max_table_rows*2} rows):**\n{table_text}")

    tables_text = "\n\n".join(all_tables) if all_tables else "No relevant tables found."
    return text, tables_text


# ✅ Step 2: Token-Aware Chunking
def split_into_paragraphs(text):
    """Splits text while keeping structure (headings, bullet points, paragraphs)."""
    paragraphs = re.split(r'\n\s*\n+', text)  
    return [p.strip() for p in paragraphs if p.strip()]  

def token_limited_chunking(text, max_tokens=160000, overlap=500):
    """Dynamically chunks text while ensuring total token count stays within limits."""
    enc = tiktoken.get_encoding("cl100k_base")  
    paragraphs = re.split(r'\n\s*\n+', text)  
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        token_count = len(enc.encode(para))  

        if current_length + token_count > max_tokens:
            chunks.append(enc.decode(enc.encode("\n\n".join(current_chunk))))
            current_chunk = current_chunk[-overlap:]  
            current_length = sum(len(enc.encode(p)) for p in current_chunk)

        current_chunk.append(para)
        current_length += token_count

    if current_chunk:
        chunks.append(enc.decode(enc.encode("\n\n".join(current_chunk))))

    return chunks


# ✅ Step 3: Summarize Chunks (Reduce API Calls)
def summarize_chunks(document_chunks, batch_size=10):
    """Merges every batch_size chunks to reduce total requests."""
    merged_chunks = []
    
    for i in range(0, len(document_chunks), batch_size):
        batch = document_chunks[i:i + batch_size]
        merged_chunks.append("\n\n".join(batch))
    
    return merged_chunks

# ✅ Step 4: Ensure Prompt Stays Within Token Limit
def prepare_prompt(chunk_data):
    """Ensures prompt stays within DeepSeek-R1 token limits before sending request."""
    enc = tiktoken.get_encoding("cl100k_base")
    
    base_prompt = PROMPT_TEMPLATE.format(
        chunk_number=chunk_data["chunk_number"],
        total_chunks=chunk_data["total_chunks"],
        document_context=chunk_data["document_context"],
        document_tables=chunk_data["document_tables"],
        previous_summaries=chunk_data["previous_summaries"]
    )

    total_tokens = len(enc.encode(base_prompt))
    
    # ✅ If prompt is still too big, trim tables first
    if total_tokens > 160000:
        print(f"Trimming oversized tables (Total Tokens: {total_tokens})")
        chunk_data["document_tables"] = "Tables removed due to token limit."

    # ✅ If still too big, remove older summaries
    total_tokens = len(enc.encode(base_prompt))
    if total_tokens > 160000:
        print(f"Trimming older summaries (Total Tokens: {total_tokens})")
        chunk_data["previous_summaries"] = "Summary history removed to fit within limits."

    return PROMPT_TEMPLATE.format(
        chunk_number=chunk_data["chunk_number"],
        total_chunks=chunk_data["total_chunks"],
        document_context=chunk_data["document_context"],
        document_tables=chunk_data["document_tables"],
        previous_summaries=chunk_data["previous_summaries"]
    )


# ✅ Step 5: Process Individual Chunks
def process_chunk(chunk_data):
    """Sends a single chunk to DeepSeek API."""
    formatted_prompt = prepare_prompt(chunk_data)

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek/deepseek-r1-zero:free", "prompt": formatted_prompt, "max_tokens": 1024}
    response = requests.post(DEEPSEEK_URL, headers=headers, json=payload)
    print(f"Response from deepseek: {response.json()}")
    return response.json().get("choices", [{}])[0].get("text", "").strip() if response.status_code == 200 else f"Error: {response.json()}"

# ✅ Step 6: Parallel Execution
def send_to_deepseek_parallel(user_query, document_chunks, document_tables, max_workers=10):
    """Processes document chunks in parallel to speed up execution."""
    total_chunks = len(document_chunks)
    previous_summaries = []
    final_responses = []

    chunk_data_list = [
        {
            "chunk_number": i + 1,
            "total_chunks": total_chunks,
            "document_context": document_chunks[i],
            "document_tables": document_tables,
            "previous_summaries": "\n\n".join(previous_summaries[-3:])
        }
        for i in range(total_chunks)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        print(f"Sending {total_chunks} chunks to DeepSeek API...")
        results = list(executor.map(process_chunk, chunk_data_list))

    return "\n\n".join(results)

# ✅ Step 7: Final Execution
pdf_path = "../../../artifacts/arch/rules1.pdf"  
user_query = "Extract the rules from this document in a form which can be used to verify against a transactional dataset of a user"

# ✅ Extract Text & Token-Limited Tables
extracted_text, extracted_tables = extract_text_and_tables(pdf_path, max_table_rows=5)

# ✅ Ensure Chunks Fit Within Token Limit
optimized_chunks = token_limited_chunking(extracted_text, max_tokens=160000, overlap=500)

# ✅ Summarize Chunks in Groups of 10
optimized_chunks = summarize_chunks(optimized_chunks, batch_size=10)

# ✅ Send to DeepSeek with Auto-Trimming
deepseek_response = send_to_deepseek_parallel(user_query, optimized_chunks, extracted_tables, max_workers=10)

# ✅ Print Final Output
print("Final Extracted Compliance Rules:\n", deepseek_response)