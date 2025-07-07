import streamlit as st

# Securely load OpenAI API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai"]["api_key"]

# Path to your reference data directory (as before)
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
