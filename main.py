import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OSIRIS Chatbot Gateway")

OPENROUTER_API_KEY = os.getenv("OpenRouter")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def health_check():
    return {"status": "online", "engine": "OSIRIS Text Gateway"}

@app.post("/api/v1/council/chat")
async def chat_endpoint(payload: ChatRequest):
    if not OPENROUTER_API_KEY:
        logger.error("OpenRouter variable missing in Railway configuration.")
        raise HTTPException(status_code=500, detail="Server configuration missing.")
        
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        openrouter_payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {"role": "system", "content": "You are the OSIRIS AI agent. Respond directly and clearly."},
                {"role": "user", "content": payload.message}
            ]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=openrouter_payload,
            timeout=15.0
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="AI gateway connection dropped.")
            
        ai_response = response.json()['choices'][0]['message']['content']
        return {"status": "success", "response": ai_response}
        
    except Exception as e:
        logger.error(f"Error processing chat routing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal routing fault.")

if __name__ == "__main__":
    import uvicorn
    target_port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=target_port)
