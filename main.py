import os
import logging
import base64
import io
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import psycopg2
from pypdf import PdfReader

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OSIRIS Backend Core")

# Environment Variable Resolution
OPENROUTER_API_KEY = os.getenv("OpenRouter")
DATABASE_URL = os.getenv("DATABASE_URL")

# Request Schema
class ProcessRequest(BaseModel):
    file_name: str
    file_data: str  # Base64 encoded PDF string
    prompt: str

@app.on_event("startup")
def startup_db_check():
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable is missing!")
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        logger.info("Database connection verified successfully on startup.")
    except Exception as e:
        logger.error(f"Database connection failed on startup: {str(e)}")

@app.post("/api/v1/council/convocate")
async def process_document(payload: ProcessRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API configuration missing on server.")
        
    try:
        logger.info(f"Processing file: {payload.file_name}")
        
        # Decode PDF content from base64 string
        pdf_bytes = base64.b64decode(payload.file_data)
        
        # Extract text safely from incoming file payload
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
        
        if not extracted_text.strip():
            extracted_text = "[No legible text content extracted from the document layout]"
            
        logger.info("Sending request to OpenRouter...")
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        openrouter_payload = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [
                {"role": "system", "content": "You are the OSIRIS AI engine. Analyze the context and follow instructions precisely."},
                {"role": "user", "content": f"Context data:\n{extracted_text}\n\nInstruction: {payload.prompt}"}
            ]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=openrouter_payload
        )
        
        if response.status_code != 200:
            logger.error(f"OpenRouter Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"OpenRouter upstream failure: {response.text}")
            
        result_json = response.json()
        ai_response = result_json['choices'][0]['message']['content']
        
        return {"status": "success", "response": ai_response}
        
    except Exception as e:
        logger.error(f"Pipeline processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
