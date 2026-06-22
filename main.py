import os
import logging
import base64
import io
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import psycopg2
from pypdf import PdfReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OSIRIS Backend Core")

OPENROUTER_API_KEY = os.getenv("OpenRouter")
DATABASE_URL = os.getenv("DATABASE_URL")

class ProcessRequest(BaseModel):
    file_name: str
    file_data: str
    prompt: str

def verify_db():
    if not DATABASE_URL:
        return False
    try:
        # Open and immediately close to avoid thread starvation
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database handshake skipped or timed out: {e}")
        return False

@app.on_event("startup")
def startup_db_check():
    verify_db()

@app.post("/api/v1/council/convocate")
async def process_document(payload: ProcessRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key missing.")
        
    try:
        logger.info(f"Processing payload stream for: {payload.file_name}")
        pdf_bytes = base64.b64decode(payload.file_data)
        
        extracted_text = ""
        with io.BytesIO(pdf_bytes) as pdf_file:
            reader = PdfReader(pdf_file)
            max_pages = min(len(reader.pages), 5)
            for i in range(max_pages):
                text = reader.pages[i].extract_text()
                if text:
                    extracted_text += text + "\n"

        if not extracted_text.strip():
            extracted_text = "[No text content found inside target file layout]"
            
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        openrouter_payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {"role": "system", "content": "You are the OSIRIS AI core. Process the context strictly."},
                {"role": "user", "content": f"Context:\n{extracted_text[:4000]}\n\nInstruction: {payload.prompt}"}
            ]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=openrouter_payload,
            timeout=15.0
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Upstream completion failure.")
            
        ai_response = response.json()['choices'][0]['message']['content']
        return {"status": "success", "response": ai_response}
        
    except Exception as e:
        logger.error(f"Request dropped safely: {str(e)}")
        raise HTTPException(status_code=500, detail="Server pipeline execution break.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
