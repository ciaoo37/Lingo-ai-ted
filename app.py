import streamlit as st
import pandas as pd
import json
import os
import random
from google import genai
from google.genai import types

st.set_page_config(page_title="LingoAI - Tedesco", page_icon="🧠", layout="wide")

DATA_FILE = "flashcards.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

if 'flashcards' not in st.session_state:
    st.session_state.flashcards = load_data()

st.sidebar.title("⚙️ Impostazioni")
api_key = st.sidebar.text_input("Inserisci la tua Google Gemini API Key", type="password")

menu = st.sidebar.radio("Menu", ["📚 Dashboard & Gestione", "✨ Genera con AI", "📖 Smart Reader", "🧠 Modalità Studio"])

# ... rest of the code
