import requests
import pdfplumber
import tiktoken
from pdfminer.high_level import extract_text
import pandas as pd
import json
import re

# API Details
API_KEY = "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"
DEEPSEEK_URL = "https://openrouter.ai/api/v1/completions"

# Prompt Template
PROMPT_TEMPLATE = """
You are a financial compliance expert analyzing a regulatory document.
This is part {chunk_number} of {total_chunks} from a larger document. 

Use the provided context to extract key financial compliance rules. 
If rules refer to tables, reference them correctly. If context is incomplete, state it clearly.  

Query: Extract the rules from this document in a form which can be used to verify against a transactional dataset of a user.

Context (Part {chunk_number} of {total_chunks}): 
{document_context}

Summary of Previous Chunks (if available): 
{previous_summaries}

Extracted Compliance Rules:
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
def split_into_paragraphs(text):
    """Splits text while keeping structure (headings, bullet points, paragraphs)."""
    paragraphs = re.split(r'\n\s*\n+', text)  # Split at blank lines (paragraphs)
    return [p.strip() for p in paragraphs if p.strip()]  # Remove empty elements

def context_preserving_chunking(text, max_tokens=2000, overlap=300):
    """
    Splits text into structured chunks while keeping headings and paragraphs together.
    Ensures rules aren't split and maintains context between API calls.
    """
    enc = tiktoken.get_encoding("cl100k_base")  # Use DeepSeek-compatible tokenizer
    paragraphs = split_into_paragraphs(text)  # Split into logical sections

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        token_count = len(enc.encode(para))  # Get token count

        if current_length + token_count > max_tokens:  # If chunk is too big, start new one
            chunks.append(enc.decode(enc.encode("\n\n".join(current_chunk))))  # Convert back to text
            current_chunk = current_chunk[-overlap:]  # Keep overlap
            current_length = sum(len(enc.encode(p)) for p in current_chunk)

        current_chunk.append(para)
        current_length += token_count

    # Add the last chunk
    if current_chunk:
        chunks.append(enc.decode(enc.encode("\n\n".join(current_chunk))))

    return chunks

# Step 3: Send Processed Text to DeepSeek-R1
def send_to_deepseek(user_query, document_chunks):
    total_chunks = len(document_chunks)
    previous_summaries = []  # Store extracted summaries for continuity
    final_responses = []

    # Process chunks in batches of 1000
    batch_size = 1000  
    for batch_start in range(0, total_chunks, batch_size):
        batch_end = min(batch_start + batch_size, total_chunks)
        batch_chunks = document_chunks[batch_start:batch_end]  # Get a batch of 1000 chunks

        print(f"Processing batch {batch_start // batch_size + 1} ({batch_start + 1} to {batch_end})...")

        formatted_prompt = PROMPT_TEMPLATE.format(
            chunk_number=batch_start + 1, total_chunks=total_chunks,
            document_context="\n\n".join(batch_chunks),  # Merge the 1000 chunks into one
            previous_summaries="\n\n".join(previous_summaries[-3:])  # Keep last 3 summaries
        )

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
        answer = response.json().get("choices", [{}])[0].get("text", "").strip() if response.status_code == 200 else f"Error: {response.json()}"
        print("#####################################################################################")
        print(answer)
        # Store the extracted summary
        previous_summaries.append(answer)
        final_responses.append(answer)

    return "\n\n".join(final_responses)  # Combine all parts into a final report


# Example Usage
pdf_path = "../../../artifacts/arch/rules.pdf"  # Replace with actual PDF file path
user_query = "Extract the rules from this document in a form which can be used to verify against a transactional dataset of a user"

# Processing
# Extract PDF text & tables
extracted_text, extracted_tables = extract_text_and_tables(pdf_path)

# Generate structured chunks
document_chunks = context_preserving_chunking(extracted_text, max_tokens=2000, overlap=300)

# Send to DeepSeek with memory of previous parts
deepseek_response = send_to_deepseek(user_query, document_chunks)

print("Final Extracted Compliance Rules:\n", deepseek_response)

