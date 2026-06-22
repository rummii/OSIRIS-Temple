from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="OSIRIS Temple Production Core")

# Grab the connection URL dynamically (Fall back to empty string if not set yet)
DATABASE_URL = os.getenv("DATABASE_URL", "YOUR_PASTED_DATABASE_URL_HERE")

class CouncilQuery(BaseModel):
    user_id: str
    user_prompt: str
    image_b64: Optional[str] = None
    extracted_text: Optional[str] = None

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Connection Failure: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "online", "system": "OSIRIS Temple Gateway"}

@app.post("/api/v1/council/convocate")
async def convocate_council(payload: CouncilQuery, authorization: Optional[str] = Header(None)):
    # 1. Connect to our newly created tables
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 2. Check Credit Wallet balance
    cur.execute("SELECT credits_remaining FROM user_profiles WHERE user_id = %s;", (payload.user_id,))
    user_row = cur.fetchone()
    
    if not user_row:
        # Auto-provision a free tier profile entry if they don't exist yet for testing
        cur.execute(
            "INSERT INTO user_profiles (user_id, credits_remaining) VALUES (%s, 1000) RETURNING credits_remaining;", 
            (payload.user_id,)
        )
        conn.commit()
        credits_available = 1000
    else:
        credits_available = user_row["credits_remaining"]
        
    if credits_available <= 0:
        cur.close()
        conn.close()
        raise HTTPException(status_code=402, detail="Insufficient credits in OSIRIS account balance.")

    # 3. Dynamic Brain Ingestion (Pull prompts directly from our live training database rows)
    cur.execute("SELECT role_id, system_instruction FROM osiris_agent_roles WHERE is_active = TRUE;")
    roles_rows = cur.fetchall()
    
    instructions = {row['role_id']: row['system_instruction'] for row in roles_rows}
    architect_sys = instructions.get('architect', 'You are The Architect.')
    engineer_sys = instructions.get('engineer', 'You are The Engineer.')
    critic_sys = instructions.get('critic', 'You are The Critic.')

    # 4. Formulate the composite prompt layout
    combined_prompt = payload.user_prompt
    if payload.extracted_text:
        combined_prompt = f"--- ATTACHED DOCUMENT CONTEXT ---\n{payload.extracted_text}\n---------------------------------\n\nUser Question: {payload.user_prompt}"
    
    content_blocks = [{"type": "text", "text": combined_prompt}]
    
    # 5. Connect to the OpenRouter pipeline
    OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_KEY_HERE")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}

    def call_engine(model_string, system_role, user_content):
        body = {
            "model": model_string,
            "messages": [
                {"role": "system", "content": system_role},
                {"role": "user", "content": user_content}
            ]
        }
        try:
            res = requests.post(url, headers=headers, json=body, timeout=30)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content'].strip()
            return f"API Error ({res.status_code}): {res.text}"
        except Exception as e:
            return f"Pipeline connection failed: {str(e)}"

    # Fire concurrent endpoints
    arch_res = call_engine("google/gemini-2.5-flash", architect_sys, content_blocks)
    
    eng_content = content_blocks.copy()
    if payload.image_b64:
        eng_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{payload.image_b64}"}})
    eng_res = call_engine("openai/gpt-4o", engineer_sys, eng_content)
    
    crit_res = call_engine("deepseek/deepseek-chat", critic_sys, content_blocks)

    # 6. Deduct credit metric charge upon calculation completion (Standard deduction baseline = 10 credits)
    cost_deduction = 10
    cur.execute(
        "UPDATE user_profiles SET credits_remaining = credits_remaining - %s WHERE user_id = %s RETURNING credits_remaining;",
        (cost_deduction, payload.user_id)
    )
    updated_row = cur.fetchone()
    conn.commit()
    
    cur.close()
    conn.close()

    return {
        "architect": arch_res,
        "engineer": eng_res,
        "critic": crit_res,
        "credits_remaining": updated_row["credits_remaining"] if updated_row else 0
    }
