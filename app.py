import streamlit as st
import requests
import base64

# Connect directly to your healthy backend engine
BACKEND_URL = "https://osiris-temple-production.up.railway.app"

st.set_page_config(page_title="OSIRIS Council Chambers", layout="wide")

st.title("🏛️ OSIRIS Council Chambers")
st.subheader("Document Processing & Analysis Pipeline")

# File Upload Processing
uploaded_file = st.file_uploader("Upload a PDF document for analysis", type=["pdf"])
user_prompt = st.text_input("Enter instructions for the council", placeholder="Summarize this document...")

if st.button("Review the attached file"):
    if not uploaded_file:
        st.warning("Please attach a document first.")
    elif not user_prompt:
        st.warning("Please provide an instruction prompt.")
    else:
        with st.spinner("Processing document through the OSIRIS pipeline..."):
            try:
                # Read file bytes and encode to base64 safely
                file_bytes = uploaded_file.read()
                base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
                
                # Format payload payload cleanly for the backend engine
                payload = {
                    "file_name": uploaded_file.name,
                    "file_data": base64_pdf,
                    "prompt": user_prompt
                }
                
                response = requests.post(f"{BACKEND_URL}/api/v1/council/convocate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("Analysis Complete!")
                    st.write(data.get("response", "No response content returned."))
                else:
                    st.error(f"Backend Server Processing Error ({response.status_code}): {response.text}")
                    
            except Exception as e:
                st.error(f"Failed to connect to the backend node: {str(e)}")
