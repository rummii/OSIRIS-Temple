import streamlit as st
import requests

BACKEND_URL = "https://osiris-temple-production.up.railway.app"

st.set_page_config(page_title="OSIRIS Council Chambers", layout="wide")

st.title("🏛️ OSIRIS Council Chambers")
st.subheader("Text-Only Chatbot Agent Baseline")

user_message = st.text_input("Message the Council:", placeholder="Type your inquiry here...")

if st.button("Send Message"):
    if not user_message:
        st.warning("Please enter a message first.")
    else:
        with st.spinner("Convocating with the OSIRIS core..."):
            try:
                payload = {"message": user_message}
                response = requests.post(f"{BACKEND_URL}/api/v1/council/chat", json=payload)
                
                if response.status_code == 200:
                    st.success("Response Received:")
                    st.write(response.json().get("response"))
                else:
                    st.error(f"Backend Server Error ({response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend service link: {str(e)}")
