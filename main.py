import os
import logging
import base64
import io
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from pypdf import PdfReader

# Setup core service logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OSIRIS Backend Core")

# Resolve variables directly from the target infrastructure profile
OPENROUTER_API_KEY = os.getenv("OpenRouter")

class ProcessRequest(BaseModel):
    file_name: str
    file_data: str
    prompt: str

@app.get("/")
def health_check():
    return {"status": "online", "service": "OSIRIS Core Pipeline"}

@app.post("/api/v1/council/convocate")
async def process_document(payload: ProcessRequest):
    if not OPENROUTER_API_KEY:
        logger.error("Missing OpenRouter credentials configuration setup.")
        raise HTTPException(status_code=500, detail="Server upstream configuration missing.")
        
    try:
        logger.info(f"Processing structural extraction stream for: {payload.file_name}")
        
        # Safe stream decoding handling
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
            extracted_text = "[Raw structural layouts parsing failure]"
            
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        openrouter_payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {"role": "system", "content": "You are the OSIRIS AI engine. Process the context safely."},
                {"role": "user", "content": f"Context:\n{extracted_text[:3000]}\n\nInstruction: {payload.prompt}"}
            ]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=openrouter_payload,
            timeout=15.0
        )
        
        if response.status_code != 200:
            logger.error(f"Upstream provider response error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Gateway processing timeout.")
            
        ai_response = response.json()['choices'][0]['message']['content']
        return {"status": "success", "response": ai_response}
        
    except Exception as e:
        logger.error(f"Data stream processing dropped cleanly: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing sequence fault.")

if __name__ == "__main__":
    import uvicorn
    # Enforce exact variable mapping for Railway's runtime proxy layer
    target_port = int(os.getenv("PORT", 8080))
    logger.info(f"Binding Core Application layer securely onto dynamic port assignment: {target_port}")
    uvicorn.run(app, host="0.0.0.0", port=target_port)
