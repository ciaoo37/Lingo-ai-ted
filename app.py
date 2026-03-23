import streamlit as st
import pandas as pd
import json
import os
import random
import uuid
import google.generativeai as genai

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LingoAI - Tedesco", page_icon="🇩🇪", layout="centered")

# --- CUSTOM CSS (Design Moderno, Mobile First) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #f3f4f6;
    }

    /* Stile della Flashcard Bianca */
    .flashcard {
        background-color: #ffffff;
        border-radius: 24px;
        padding: 2.5rem 1.5rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
        text-align: center;
        margin: 1rem auto 2rem auto;
        border: 1px solid #e5e7eb;
        max-width: 100%;
    }
    
    .fc-category {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #dc2626;
        font-weight: 800;
        margin-bottom: 1rem;
    }
    
    .fc-german {
        font-size: 2.8rem;
        font-weight: 800;
        color: #000000;
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }
    
    .fc-italian {
        font-size: 1.8rem;
        font-weight: 600;
        color: #4b5563;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 2px dashed #e5e7eb;
    }
    
    .fc-example {
        margin-top: 1.5rem;
        padding: 1rem;
        background-color: #f9fafb;
        border-radius: 16px;
        font-size: 1.1rem;
        color: #374151;
        font-style: italic;
        border-left: 4px solid #dc2626;
    }

    /* Stile Bottoni Grandi e Colorati */
    div[data-testid="stButton"] button {
        border-radius: 20px;
        font-weight: 800;
        height: 4rem;
        font-size: 1.1rem;
        width: 100%;
        transition: transform 0.1s;
    }
    
    div[data-testid="stButton"] button:active {
        transform: scale(0.95);
    }

    /* Colora i bottoni in base al testo */
    button:has(p:contains("✅ Sì, la so")) {
        background-color: #10b981 !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
    }
    
    button:has(p:contains("❌ No, non la so")) {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4) !important;
    }
    
    button:has(p:contains("🔄 Gira la carta")) {
        background-color: #2563eb !important; /* Blu moderno */
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIONE DATI (CSV) ---
DATA_FILE = "flashcards.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        df = pd.read_csv(DATA_FILE)
        df = df.fillna("")
        records = df.to_dict('records')
        # Assicuriamoci che ogni card abbia un ID univoco
        for r in records:
            if 'id' not in r or not r['id']:
                r['id'] = str(uuid.uuid4())
        return records
    except Exception as e:
        st.sidebar.error(f"Errore lettura CSV: {e}")
        return []

def save_data(data):
    try:
        if not data:
            pd.DataFrame(columns=['id', 'category', 'german', 'italian', 'article', 'plural', 'exampleSentenceGerman', 'exampleSentenceItalian', 'correctCount', 'incorrectCount']).to_csv(DATA_FILE, index=False)
        else:
            pd.DataFrame(data).to_csv(DATA_FILE, index=False)
    except Exception as e:
        st.error(f"Errore salvataggio CSV: {e}")

# Inizializzazione Session State
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = load_data()
if 'study_mode' not in st.session_state:
    st.session_state.study_mode = "setup" # setup, studying, summary
if 'card_flipped' not in st.session_state:
    st.session_state.card_flipped = False

# --- BARRA LATERALE ---
with st.sidebar:
    st.title("⚙️ Impostazioni")
    api_key = st.text_input("🔑 API Key Gemini", type="password")
    
    st.markdown("---")
    menu = st.radio(
        "📍 Navigazione", 
        ["📊 Dashboard & Gestione", "✨ Genera Flashcard", "🧠 Modalità Studio"]
    )

if api_key:
    genai.configure(api_key=api_key)

# --- VISTA: DASHBOARD & GESTIONE (CRUD) ---
if menu == "📊 Dashboard & Gestione":
    st.title("📊 Dashboard & Gestione")
    
    if not st.session_state.flashcards:
        st.info("Non hai ancora flashcard. Vai su 'Genera Flashcard' per iniziare.")
    else:
        st.success(f"Hai **{len(st.session_state.flashcards)}** flashcard nel database.")
        
        st.markdown("### ✏️ Modifica o Elimina")
        # Creiamo un dizionario per la selectbox
        card_options = {c['id']: f"{c.get('article', '')} {c['german']} ➔ {c['italian']}" for c in st.session_state.flashcards}
        
        selected_id = st.selectbox("Seleziona una flashcard da gestire:", options=list(card_options.keys()), format_func=lambda x: card_options[x])
        
        if selected_id:
            # Trova la card
            card_idx = next((index for (index, d) in enumerate(st.session_state.flashcards) if d["id"] == selected_id), None)
            card = st.session_state.flashcards[card_idx]
            
            with st.expander("Modifica i dettagli della card", expanded=True):
                with st.form(f"edit_form_{selected_id}"):
                    new_ger = st.text_input("Tedesco", value=card.get('german', ''))
                    new_ita = st.text_input("Italiano", value=card.get('italian', ''))
                    new_cat = st.text_input("Categoria", value=card.get('category', ''))
                    new_ex_de = st.text_area("Esempio (Tedesco)", value=card.get('exampleSentenceGerman', ''))
                    new_ex_it = st.text_area("Esempio (Italiano)", value=card.get('exampleSentenceItalian', ''))
                    
                    col_save, col_del = st.columns(2)
                    submit_save = col_save.form_submit_button("💾 Salva Modifiche")
                    submit_del = col_del.form_submit_button("🗑️ Elimina Card")
                    
                    if submit_save:
                        st.session_state.flashcards[card_idx].update({
                            'german': new_ger, 'italian': new_ita, 'category': new_cat,
                            'exampleSentenceGerman': new_ex_de, 'exampleSentenceItalian': new_ex_it
                        })
                        save_data(st.session_state.flashcards)
                        st.success("Modifiche salvate!")
                        st.rerun()
                        
                    if submit_del:
                        st.session_state.flashcards.pop(card_idx)
                        save_data(st.session_state.flashcards)
                        st.warning("Card eliminata!")
                        st.rerun()

# --- VISTA: GENERA CON AI ---
elif menu == "✨ Genera Flashcard":
    st.title("✨ Genera con AI")
    
    if not api_key:
        st.warning("⚠️ Inserisci la tua API Key nella barra laterale per iniziare.")
    else:
        st.write("Incolla una lista di parole. L'AI creerà card complete di frasi d'esempio naturali.")
        words_input = st.text_area("Lista parole (una per riga):", height=150)
        
        if st.button("🚀 Genera Flashcard"):
            if not words_input.strip():
                st.warning("Inserisci almeno una parola.")
            else:
                with st.spinner("L'AI sta creando le tue card..."):
                    try:
                        # Modello aggiornato come richiesto
                        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                        prompt = f"""
                        Genera flashcard in italiano e tedesco per queste parole:
                        {words_input}
                        
                        Devi includere obbligatoriamente: Termine, Traduzione, Categoria e una Frase d'esempio naturale.
                        Restituisci ESATTAMENTE un array JSON valido.
                        Struttura per ogni parola:
                        {{
                            "id": "",
                            "category": "Sostantivi, Verbi, ecc.",
                            "german": "parola in tedesco",
                            "italian": "traduzione in italiano",
                            "article": "articolo determinativo se è un sostantivo, altrimenti vuoto",
                            "plural": "forma plurale se è un sostantivo, altrimenti vuoto",
                            "exampleSentenceGerman": "frase di esempio naturale in tedesco",
                            "exampleSentenceItalian": "traduzione della frase in italiano"
                        }}
                        """
                        response = model.generate_content(
                            prompt,
                            generation_config=genai.GenerationConfig(response_mime_type="application/json")
                        )
                        
                        testo_json = response.text.strip()
                        if testo_json.startswith("```json"):
                            testo_json = testo_json[7:-3]
                            
                        new_cards = json.loads(testo_json.strip())
                        
                        for card in new_cards:
                            card['id'] = str(uuid.uuid4())
                            card['correctCount'] = 0
                            card['incorrectCount'] = 0
                            
                        st.session_state.flashcards.extend(new_cards)
                        save_data(st.session_state.flashcards)
                        st.success(f"🎉 {len(new_cards)} flashcard aggiunte!")
                    except Exception as e:
                        st.error(f"Errore durante la generazione: {e}")

# --- VISTA: MODALITÀ STUDIO ---
elif menu == "🧠 Modalità Studio":
    st.title("🧠 Modalità Studio")
    
    if not st.session_state.flashcards:
        st.info("Aggiungi prima delle flashcard!")
    else:
        # FASE 1: SETUP DELLA SESSIONE
        if st.session_state.study_mode == "setup":
            st.markdown("### Scegli come vuoi studiare oggi:")
            
            tab1, tab2 = st.tabs(["🎯 Smart Random", "✅ Selezione Manuale"])
            
            with tab1:
                st.write("L'algoritmo pescherà le parole dando priorità a quelle che sbagli più spesso.")
                num_cards = st.slider("Quante parole vuoi ripassare?", min_value=1, max_value=len(st.session_state.flashcards), value=min(10, len(st.session_state.flashcards)))
                
                if st.button("Inizia Smart Random", type="primary"):
                    # Calcola la percentuale di errore per ordinare
                    def error_rate(c):
                        tot = c.get('correctCount', 0) + c.get('incorrectCount', 0)
                        return c.get('incorrectCount', 0) / tot if tot > 0 else 0.5 # 0.5 per le parole nuove
                    
                    sorted_cards = sorted(st.session_state.flashcards, key=error_rate, reverse=True)
                    st.session_state.study_cards = sorted_cards[:num_cards]
                    st.session_state.study_index = 0
                    st.session_state.card_flipped = False
                    st.session_state.session_results = {'correct': [], 'incorrect': []}
                    st.session_state.study_mode = "studying"
                    st.rerun()
            
            with tab2:
                st.write("Spunta le singole parole che vuoi ripassare.")
                with st.form("manual_selection_form"):
                    selected_ids = []
                    for c in st.session_state.flashcards:
                        if st.checkbox(f"{c['german']} ({c['italian']})", key=f"chk_{c['id']}"):
                            selected_ids.append(c['id'])
                    
                    if st.form_submit_button("Inizia Selezione Manuale"):
                        if not selected_ids:
                            st.warning("Seleziona almeno una parola!")
                        else:
                            st.session_state.study_cards = [c for c in st.session_state.flashcards if c['id'] in selected_ids]
                            random.shuffle(st.session_state.study_cards)
                            st.session_state.study_index = 0
                            st.session_state.card_flipped = False
                            st.session_state.session_results = {'correct': [], 'incorrect': []}
                            st.session_state.study_mode = "studying"
                            st.rerun()

        # FASE 2: STUDIO ATTIVO
        elif st.session_state.study_mode == "studying":
            if st.session_state.study_index < len(st.session_state.study_cards):
                card = st.session_state.study_cards[st.session_state.study_index]
                
                st.progress((st.session_state.study_index) / len(st.session_state.study_cards))
                st.caption(f"Carta {st.session_state.study_index + 1} di {len(st.session_state.study_cards)}")
                
                if not st.session_state.card_flipped:
                    # FRONTE
                    st.markdown(f"""
                    <div class="flashcard">
                        <div class="fc-category">{card.get('category', '')}</div>
                        <div class="fc-german">{card.get('article', '')} {card.get('german', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🔄 Gira la carta"):
                        st.session_state.card_flipped = True
                        st.rerun()
                else:
                    # RETRO
                    ex_de = card.get('exampleSentenceGerman', '')
                    ex_it = card.get('exampleSentenceItalian', '')
                    example_html = f'<div class="fc-example">🇩🇪 {ex_de}<br><br>🇮🇹 <span style="opacity:0.8;">{ex_it}</span></div>' if ex_de else ''
                    
                    st.markdown(f"""
                    <div class="flashcard">
                        <div class="fc-category">{card.get('category', '')}</div>
                        <div class="fc-german">{card.get('article', '')} {card.get('german', '')}</div>
                        <div class="fc-italian">🇮🇹 {card.get('italian', '')}</div>
                        {example_html}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    # Trova indice nel DB principale per aggiornare le statistiche globali
                    db_idx = next((i for i, c in enumerate(st.session_state.flashcards) if c['id'] == card['id']), -1)
                    
                    with col1:
                        if st.button("❌ No, non la so"):
                            if db_idx != -1:
                                st.session_state.flashcards[db_idx]['incorrectCount'] = int(st.session_state.flashcards[db_idx].get('incorrectCount', 0)) + 1
                                save_data(st.session_state.flashcards)
                            st.session_state.session_results['incorrect'].append(card)
                            st.session_state.study_index += 1
                            st.session_state.card_flipped = False
                            st.rerun()
                            
                    with col2:
                        if st.button("✅ Sì, la so"):
                            if db_idx != -1:
                                st.session_state.flashcards[db_idx]['correctCount'] = int(st.session_state.flashcards[db_idx].get('correctCount', 0)) + 1
                                save_data(st.session_state.flashcards)
                            st.session_state.session_results['correct'].append(card)
                            st.session_state.study_index += 1
                            st.session_state.card_flipped = False
                            st.rerun()
            else:
                # Fine carte, passa al riepilogo
                st.session_state.study_mode = "summary"
                st.rerun()

        # FASE 3: RIEPILOGO E CICLO DI FINE STUDIO
        elif st.session_state.study_mode == "summary":
            st.balloons()
            st.markdown("<h2 style='text-align: center;'>Sessione Completata! 🎉</h2>", unsafe_allow_html=True)
            
            corrette = len(st.session_state.session_results['correct'])
            sbagliate = len(st.session_state.session_results['incorrect'])
            
            col1, col2 = st.columns(2)
            col1.metric("✅ Corrette", corrette)
            col2.metric("❌ Da ripassare", sbagliate)
            
            st.markdown("---")
            
            if sbagliate > 0:
                if st.button("🔄 Ripeti solo quelle che non sapevo"):
                    st.session_state.study_cards = st.session_state.session_results['incorrect']
                    random.shuffle(st.session_state.study_cards)
                    st.session_state.study_index = 0
                    st.session_state.card_flipped = False
                    st.session_state.session_results = {'correct': [], 'incorrect': []}
                    st.session_state.study_mode = "studying"
                    st.rerun()
            
            if st.button("🏠 Esci e torna alla Dashboard"):
                st.session_state.study_mode = "setup"
                st.rerun()
