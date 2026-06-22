import streamlit as st
import requests
import base64
from pypdf import PdfReader

# Only the backend URL is needed on the frontend
BACKEND_URL = "https://osiris-temple-production.up.railway.app"

st.set_page_config(page_title="OSIRIS Temple Admin Console", layout="wide")
