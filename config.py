import streamlit as st

def get_openai_api_key():
    return st.secrets["openai"]["api_key"]


# Path to your reference data directory (as before)
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
