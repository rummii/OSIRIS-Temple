import streamlit as st
import requests
import json
import base64
from pypdf import PdfReader

st.set_page_config(page_title="OSIRIS Temple Admin Console", layout="wide", initial_sidebar_state="expanded")

# Dark Temple Theme Customization
st.markdown("""
    <style>
    .main { background-color: #0d0d0f; }
    div[data-testid="stSidebar"] { background-color: #131317; border-right: 1px solid #232329; }
    .stTextInput>div>div>input { background-color: #0d0d0f; color: white; border: 1px solid #232329; }
    div[data-testid="stStatusWidget"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# Point directly to your local FastAPI backend instance running on port 8000
BACKEND_URL = "https://osiris-temple-production.up.railway.app"


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Fallback test ID for administrative operations
if "user_id" not in st.session_state:
    st.session_state.user_id = "admin_jet_01"

with st.sidebar:
    st.title("🏛️ Temple Core")
    st.caption("OSIRIS Production Management Console")
    st.markdown("---")
    
    # Active User Profile Status Block
    st.subheader("👤 Profile Metrics")
    st.info(f"**User ID:** {st.session_state.user_id}")
    
    st.markdown("---")
    
    # Multi-Format Attachment Upload Engine
    uploaded_file = st.file_uploader(
        "📎 Ingest Asset Document", 
        type=["png", "jpg", "jpeg", "txt", "py", "md", "pdf"]
    )
    
    image_payload = None
    doc_text_context = ""
    
    if uploaded_file is not None:
        file_name = uploaded_file.name.lower()
        if file_name.endswith(('.png', '.jpg', '.jpeg')):
            st.image(uploaded_file, caption="Staged Image Asset", use_container_width=True)
            image_payload = base64.b64encode(uploaded_file.read()).decode("utf-8")
        elif file_name.endswith('.pdf'):
            try:
                pdf_reader = PdfReader(uploaded_file)
                text_accum = []
                for page in pdf_reader.pages:
                    if page_text := page.extract_text():
                        text_accum.append(page_text)
                doc_text_context = "\n".join(text_accum)
                st.success(f"Parsed PDF Context successfully.")
            except Exception as e:
                st.error(f"PDF parsing failure: {str(e)}")
        else:
            try:
                doc_text_context = uploaded_file.read().decode("utf-8")
                st.success(f"Code/Text file context loaded.")
            except Exception as e:
                st.error(f"File read failure: {str(e)}")

st.title("🔮 OSIRIS Council Chambers")
st.caption("Production Multi-Agent Pipeline Gateway via Railway PostgreSQL Database")

# Render persistent session text matrix
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

if user_query := st.chat_input("Convocate Council query matrix..."):
    st.session_state.chat_history.append(("user", user_query))
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.spinner("Streaming response matrix across the multi-agent array..."):
        # Packaging payload matching your FastAPI baseline definition layout
        payload = {
            "user_id": st.session_state.user_id,
            "user_prompt": user_query,
            "image_b64": image_payload,
            "extracted_text": doc_text_context
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/api/v1/council/convocate", json=payload, timeout=40)
            
            if response.status_code == 200:
                data = response.json()
                
                osiris_msg = f"""🏛️ **OSIRIS: Unified Multi-Agent Response**

* **Architect Analysis (Gemini):** {data.get('architect', 'N/A')}

* **Engineer Analysis (ChatGPT):** {data.get('engineer', 'N/A')}

* **Critic Analysis (DeepSeek):** {data.get('critic', 'N/A')}

---
💰 *Transaction Complete. Remaining Balance Wallet Credits:* **{data.get('credits_remaining', '0')}**"""
                
                st.session_state.chat_history.append(("assistant", osiris_msg))
                with st.chat_message("assistant"):
                    st.markdown(osiris_msg)
            else:
                st.error(f"Backend Server Processing Error ({response.status_code}): {response.text}")
        except Exception as e:
            st.error(f"Could not connect to FastAPI Core Engine at {BACKEND_URL}. Verification error: {str(e)}")
