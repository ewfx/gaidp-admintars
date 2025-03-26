from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import os
import tempfile
from document_processor import DocumentProcessor
from rule_generator import RuleGenerator
from validator import DataValidator
from risk_engine import RiskEngine
from remediation import RemediationEngine
import pandas as pd

from deepseek_adapter import DeepSeekAdapter
from document_processor import DocumentProcessor
from rule_generator import RuleGenerator
# ... other imports ...

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Configuration
DEEPSEEK_API_KEY = "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"

# Initialize components with DeepSeek
doc_processor = DocumentProcessor(DEEPSEEK_API_KEY)
rule_generator = RuleGenerator(DEEPSEEK_API_KEY)
validator = DataValidator()
risk_engine = RiskEngine()
remediation_engine = RemediationEngine()

class ProcessRequest(BaseModel):
    text: str = None
    file_url: str = None

class ValidationRequest(BaseModel):
    rules: List[Dict]
    data: List[Dict]

@app.post("/api/process")
async def process_regulations(request: ProcessRequest):
    try:
        if request.text:
            regulatory_text = request.text
        elif request.file_url:
            regulatory_text = doc_processor.process_uploaded_file(request.file_url)
        else:
            raise HTTPException(status_code=400, detail="Either text or file_url must be provided")
        
        print("In app.py")
        requirements = doc_processor.extract_regulatory_requirements(regulatory_text)
        rules = rule_generator.generate_profiling_rules(requirements)
        validation_code = rule_generator.generate_executable_code(rules)
        
        return {
            "requirements": requirements,
            "rules": rules,
            "validation_code": validation_code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate")
async def validate_data(request: ValidationRequest):
    try:
        validator = DataValidator(DEEPSEEK_API_KEY)  # Pass API key
        
        # Convert data to list if it's not already
        data = request.data if isinstance(request.data, list) else [request.data]
        
        # Get LLM-powered validation results
        results = await validator.validate_transactions(data, request.rules)
        
        # Convert risk assessment to DataFrame for consistency
        risk_df = pd.DataFrame(results['risk_assessment']).fillna(0)
        
        return {
            "validation_results": results["validation_results"],
            "risk_assessment": risk_df.to_dict('records'),
            "remediation_actions": results["remediation_actions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Get the original file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Create a temp file with the original extension
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Process the file while preserving its type
        regulatory_text = doc_processor.process_uploaded_file(temp_path)
        
        # Clean up
        os.unlink(temp_path)
        
        return {
            "text": regulatory_text,
            "file_type": file_extension[1:],  # Remove the dot
            "original_filename": file.filename
        }
    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=str(e))
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
            print(f"Uploaded file saved to: {temp_path}")
        
        # Process the file
        regulatory_text = doc_processor.process_uploaded_file(temp_path)
        os.unlink(temp_path)  # Clean up
        
        return {"text": regulatory_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-transactions")
async def upload_transactions(file: UploadFile = File(...)):
    try:
        # Read file based on extension with dtype=str to preserve formatting
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file, dtype=str, keep_default_na=False)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file.file, dtype=str, keep_default_na=False)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Convert empty strings back to None if needed
        df = df.replace('', None)
        
        # Convert to list of dicts
        transactions = df.to_dict('records')
        
        return {
            "filename": file.filename,
            "data": transactions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)