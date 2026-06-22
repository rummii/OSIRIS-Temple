import streamlit as st
import requests

# Configuration
BACKEND_URL = "https://osiris-temple-production.up.railway.app"

st.set_page_config(page_title="OSIRIS Council Chambers", layout="wide")

# Custom Dark Theme Styling matching your layout
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stTextInput>div>div>input { background-color: #262730; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ OSIRIS Council Chambers")
st.subheader("Text-Only Chatbot Agent Baseline")

# Simplified chat layout input
user_message = st.text_input("Message the Council:", placeholder="Type your inquiry here...")

if st.button("Send Message"):
    if not user_message:
        st.warning("Please enter a message first.")
    else:
        with st.spinner("Convocating with the OSIRIS core..."):
            try:
                # Lightweight payload structure without binary files
                payload = {
                    "message": user_message
                }
                
                target_url = f"{BACKEND_URL}/api/v1/council/chat"
                response = requests.post(target_url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("Response Received:")
                    st.write(data.get("response", "No content returned."))
                else:
                    st.error(f"Backend Server Error ({response.status_code}): {response.text}")
                    
            except Exception as e:
                st.error(f"Failed to connect to the backend node: {str(e)}")
