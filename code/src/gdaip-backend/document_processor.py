import re
import os
from typing import List, Dict, Optional
from PyPDF2 import PdfReader
import pandas as pd
from deepseek_adapter import DeepSeekAdapter

class DocumentProcessor:
    def __init__(self, api_key: str):
        self.llm_adapter = DeepSeekAdapter(api_key)
        
    def extract_regulatory_requirements(self, document_text: str) -> List[Dict]:
        """Extract regulatory requirements using DeepSeek"""
        prompt = f"""
        Extract all regulatory requirements from the following banking regulation text.
        For each requirement, identify:
        1. The data fields involved
        2. The validation rules
        3. Any exceptions or special cases
        4. The json response should be strictlty JSON parsable and is a valid JSON
        
        Format the output as a JSON list where each item has:
        - "requirement": description of the requirement
        - "fields": list of data fields involved
        - "rule": the validation rule
        - "exceptions": any exceptions to the rule
        
        Regulation Text:
        {document_text}
        
        JSON Output:
        """
        
        result = self.llm_adapter.generate(prompt, temperature=0.3)
        print(f"Extracted info: {result}")
        try:
            # Clean the JSON output from LLM
            json_start = result.find('[')
            json_end = result.rfind(']') + 1

            if json_end == 0 or result[json_end - 1] != ']':
                result += '}]'
                json_end = len(result)

            json_str = result[json_start:json_end]
            return eval(json_str)
        except Exception as e:
            raise ValueError(f"Failed to parse DeepSeek output: {str(e)}")

    def process_uploaded_file(self, file_path: str) -> str:
        """Process uploaded file while respecting its type"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check extension explicitly
        if file_path.lower().endswith('.pdf'):
            return self._extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(('.csv', '.xlsx', '.xls')):
            return self._extract_text_from_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {os.path.splitext(file_path)[1]}")

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file using PyPDF2"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:  # Only add if text was extracted
                        text += page_text + "\n"
            
            if not text.strip():
                raise ValueError("No text could be extracted - document may be scanned/image-based")
                
            return self._clean_extracted_text(text)
        except Exception as e:
            raise ValueError(f"PDF text extraction failed: {str(e)}")

    def _extract_text_with_ocr(self, pdf_path: str) -> str:
        """Fallback OCR method for scanned PDFs using pytesseract"""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            text = ""
            images = convert_from_path(pdf_path)
            for i, image in enumerate(images):
                text += f"--- Page {i+1} ---\n"
                text += pytesseract.image_to_string(image) + "\n"
                
            return self._clean_extracted_text(text)
        except ImportError:
            raise ValueError("OCR dependencies not installed. Install with: pip install pytesseract pdf2image")
        except Exception as e:
            raise ValueError(f"OCR processing failed: {str(e)}")

    def extract_tables_from_pdf(self, pdf_path: str) -> List[pd.DataFrame]:
        """Extract tabular data from PDF using camelot"""
        try:
            import camelot
            tables = camelot.read_pdf(pdf_path, flavor='lattice')
            return [table.df for table in tables]
        except ImportError:
            raise ValueError("Table extraction dependencies not installed. Install with: pip install camelot-py")
        except Exception as e:
            raise ValueError(f"Table extraction failed: {str(e)}")

    def _extract_text_from_csv(self, csv_path: str) -> str:
        """Extract and format text from CSV file"""
        try:
            # Read CSV with multiple possible delimiters
            df = pd.read_csv(csv_path, sep=None, engine='python')
            
            # Convert to a readable text format
            text = "CSV Data Summary:\n"
            text += f"Columns: {', '.join(df.columns)}\n\n"
            text += "Sample Records:\n"
            
            # Add first few rows as sample
            for _, row in df.head(5).iterrows():
                text += " | ".join([str(x) for x in row]) + "\n"
                
            return text
        except Exception as e:
            raise ValueError(f"Failed to process CSV file: {str(e)}")

    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove page numbers and headers/footers (simple pattern matching)
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'\n\d+\n', '\n', text)
        
        # Clean up OCR artifacts if present
        text = re.sub(r'\x0c', '', text)  # Remove form feed characters
        text = re.sub(r'[^\S\n]+', ' ', text)  # Collapse multiple spaces
        
        return text

    def process_regulatory_document(self, file_path: str, include_tables: bool = False) -> dict:
        """
        Comprehensive document processing with optional table extraction
        Returns:
            {
                "text": extracted text content,
                "tables": list of extracted tables (if include_tables=True),
                "requirements": extracted regulatory requirements
            }
        """
        result = {"text": "", "tables": [], "requirements": []}
        
        # Extract main text content
        result["text"] = self.process_uploaded_file(file_path)
        
        # Extract tables if requested and file is PDF
        if include_tables and file_path.lower().endswith('.pdf'):
            try:
                result["tables"] = self.extract_tables_from_pdf(file_path)
            except Exception as e:
                print(f"Warning: Table extraction failed - {str(e)}")
        
        # Extract regulatory requirements
        result["requirements"] = self.extract_regulatory_requirements(result["text"])
        
        return result