import streamlit as st
import pandas as pd
import json
import os
import random
import uuid
import google.generativeai as genai

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LingoAI - Tedesco", page_icon="🇩🇪", layout="centered")

# --- CUSTOM CSS (Times New Roman, Light/Dark Mode, Card Design) ---
st.markdown("""
<style>
    /* Applica Times New Roman a tutta l'app */
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, div, span, button, input, select, textarea {
        font-family: 'Times New Roman', Times, serif !important;
    }
    
    /* Stile della Flashcard (Adattiva Light/Dark) */
    .flashcard {
        background-color: var(--secondary-background-color);
        border-radius: 24px;
        padding: 2.5rem 1.5rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        text-align: center;
        margin: 1rem auto 2rem auto;
        border: 1px solid rgba(128, 128, 128, 0.2);
        max-width: 100%;
        transition: transform 0.2s ease;
    }
    
    .fc-category {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #dc2626; /* Rosso scuro, leggibile ovunque */
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .fc-german {
        font-size: 3.2rem;
        font-weight: bold;
        color: var(--text-color);
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }
    
    .fc-italian {
        font-size: 2rem;
        font-weight: normal;
        color: var(--text-color);
        opacity: 0.85;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 2px dashed rgba(128, 128, 128, 0.3);
    }
    
    .fc-example {
        margin-top: 1.5rem;
        padding: 1rem;
        background-color: rgba(128, 128, 128, 0.1);
        border-radius: 16px;
        font-size: 1.2rem;
        color: var(--text-color);
        font-style: italic;
        border-left: 4px solid #dc2626;
    }

    /* Stile Bottoni Grandi e Colorati */
    div[data-testid="stButton"] button {
        border-radius: 16px;
        font-weight: bold;
        font-size: 1.2rem;
        width: 100%;
        height: 3.5rem;
        transition: transform 0.1s;
    }
    
    div[data-testid="stButton"] button:active {
        transform: scale(0.95);
    }

    /* Colora i bottoni in base al testo contenuto */
    button:has(p:contains("✅ Sì, la so")) {
        background-color: #10b981 !important;
        color: white !important;
        border: none !important;
    }
    
    button:has(p:contains("❌ No, non la so")) {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
    }
    
    button:has(p:contains("🔄 Gira la carta")) {
        background-color: #3b82f6 !important;
        color: white !important;
        border: none !important;
    }
    
    /* Reader Text Box */
    .reader-box {
        background-color: var(--secondary-background-color);
        padding: 2rem;
        border-radius: 16px;
        font-size: 1.3rem;
        line-height: 1.6;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIONE DATI (CSV PERSISTENTE) ---
DATA_FILE = "flashcards.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        df = pd.read_csv(DATA_FILE)
        df = df.fillna("")
        records = df.to_dict('records')
        # Assicurati che ogni record abbia un ID e il campo 'selected'
        for r in records:
            if 'id' not in r or not r['id']:
                r['id'] = str(uuid.uuid4())
            if 'selected' not in r:
                r['selected'] = False
            # Converti stringhe "True"/"False" in booleani se necessario
            if isinstance(r['selected'], str):
                r['selected'] = r['selected'].lower() == 'true'
        return records
    except Exception as e:
        st.sidebar.error(f"Errore caricamento CSV: {e}")
        return []

def save_data(data):
    try:
        if not data:
            cols = ['id', 'category', 'german', 'italian', 'article', 'plural', 'exampleSentenceGerman', 'exampleSentenceItalian', 'correctCount', 'incorrectCount', 'selected']
            pd.DataFrame(columns=cols).to_csv(DATA_FILE, index=False)
        else:
            pd.DataFrame(data).to_csv(DATA_FILE, index=False)
    except Exception as e:
        st.error(f"Errore salvataggio CSV: {e}")

# Inizializzazione Session State
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = load_data()
if 'study_phase' not in st.session_state:
    st.session_state.study_phase = "setup" # setup, active, summary
if 'card_flipped' not in st.session_state:
    st.session_state.card_flipped = False

# --- BARRA LATERALE ---
with st.sidebar:
    st.title("⚙️ Impostazioni")
    api_key = st.text_input("🔑 API Key Gemini", type="password")
    
    st.markdown("---")
    menu = st.radio(
        "📍 Navigazione", 
        ["📊 Dashboard & Gestione", "✨ Genera Flashcard", "📖 Smart Reader", "🧠 Modalità Studio"]
    )

if api_key:
    genai.configure(api_key=api_key)

# --- VISTA: DASHBOARD & GESTIONE (CRUD) ---
if menu == "📊 Dashboard & Gestione":
    st.title("📊 Dashboard & Gestione")
    
    if not st.session_state.flashcards:
        st.info("Nessuna flashcard presente. Vai su 'Genera Flashcard' per iniziare.")
    else:
        tab_lista, tab_modifica = st.tabs(["📋 Lista & Selezione Studio", "✏️ Modifica / Elimina"])
        
        with tab_lista:
            st.write("Spunta la casella **'Studia'** per selezionare manualmente le parole per la prossima sessione.")
            
            # Creiamo un DataFrame per l'editor interattivo
            df = pd.DataFrame(st.session_state.flashcards)
            cols_to_edit = ['selected', 'german', 'italian', 'category', 'correctCount', 'incorrectCount']
            
            # Mostra l'editor
            edited_df = st.data_editor(
                df[cols_to_edit],
                column_config={
                    "selected": st.column_config.CheckboxColumn("Studia", help="Seleziona per lo studio manuale", default=False),
                    "german": "Tedesco",
                    "italian": "Italiano",
                    "category": "Categoria",
                    "correctCount": "✅",
                    "incorrectCount": "❌"
                },
                disabled=["german", "italian", "category", "correctCount", "incorrectCount"],
                hide_index=True,
                use_container_width=True,
                key="data_editor"
            )
            
            # Salva le selezioni se cambiano
            if st.button("💾 Salva Selezioni"):
                for i, row in edited_df.iterrows():
                    st.session_state.flashcards[i]['selected'] = row['selected']
                save_data(st.session_state.flashcards)
                st.success("Selezioni salvate con successo!")

        with tab_modifica:
            st.write("Scegli una parola dal menu a tendina per modificarla o eliminarla.")
            options = {c['id']: f"{c.get('article', '')} {c['german']} ➔ {c['italian']}" for c in st.session_state.flashcards}
            selected_id = st.selectbox("Seleziona Flashcard:", options=list(options.keys()), format_func=lambda x: options[x])
            
            if selected_id:
                card_idx = next(i for i, c in enumerate(st.session_state.flashcards) if c["id"] == selected_id)
                card = st.session_state.flashcards[card_idx]
                
                with st.form(f"edit_form"):
                    st.subheader("Modifica Dettagli")
                    col1, col2 = st.columns(2)
                    new_ger = col1.text_input("Tedesco", value=card.get('german', ''))
                    new_ita = col2.text_input("Italiano", value=card.get('italian', ''))
                    new_cat = st.text_input("Categoria", value=card.get('category', ''))
                    new_ex_de = st.text_area("Frase d'esempio (Tedesco)", value=card.get('exampleSentenceGerman', ''))
                    new_ex_it = st.text_area("Traduzione frase", value=card.get('exampleSentenceItalian', ''))
                    
                    col_s, col_d = st.columns(2)
                    btn_save = col_s.form_submit_button("💾 Salva Modifiche")
                    btn_del = col_d.form_submit_button("🗑️ Elimina Card")
                    
                    if btn_save:
                        st.session_state.flashcards[card_idx].update({
                            'german': new_ger, 'italian': new_ita, 'category': new_cat,
                            'exampleSentenceGerman': new_ex_de, 'exampleSentenceItalian': new_ex_it
                        })
                        save_data(st.session_state.flashcards)
                        st.success("Card aggiornata!")
                        st.rerun()
                        
                    if btn_del:
                        st.session_state.flashcards.pop(card_idx)
                        save_data(st.session_state.flashcards)
                        st.warning("Card eliminata definitivamente.")
                        st.rerun()

# --- VISTA: GENERA CON AI ---
elif menu == "✨ Genera Flashcard":
    st.title("✨ Genera Flashcard con AI")
    
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
                        # Modello esplicito richiesto
                        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                        prompt = f"""
                        Genera flashcard in italiano e tedesco per queste parole:
                        {words_input}
                        
                        Devi includere obbligatoriamente: Termine, Traduzione, Categoria e una Frase d'esempio naturale.
                        Restituisci ESATTAMENTE un array JSON valido.
                        Struttura per ogni parola:
                        {{
                            "category": "Sostantivi, Verbi, Aggettivi, ecc.",
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
                            card['selected'] = False
                            
                        st.session_state.flashcards.extend(new_cards)
                        save_data(st.session_state.flashcards)
                        st.success(f"🎉 {len(new_cards)} flashcard aggiunte!")
                    except Exception as e:
                        st.error(f"Errore durante la generazione: {e}")

# --- VISTA: SMART READER ---
elif menu == "📖 Smart Reader":
    st.title("📖 Smart Reader")
    
    if not api_key:
        st.warning("⚠️ Inserisci la tua API Key nella barra laterale per iniziare.")
    elif not st.session_state.flashcards:
        st.info("Aggiungi prima delle flashcard per permettere all'AI di usare il tuo vocabolario.")
    else:
        st.write("L'AI scriverà un testo usando le parole che stai studiando.")
        
        col1, col2 = st.columns([1, 2])
        level = col1.selectbox("Livello di difficoltà", ["A1", "A2", "B1", "B2"])
        topic = col2.text_input("Tema della storia (Prompt personalizzato)", placeholder="Es: Un drago in cucina, Una giornata a Berlino...")
        
        if st.button("📚 Genera Testo"):
            if not topic.strip():
                st.warning("Inserisci un tema per la storia.")
            else:
                with st.spinner("L'AI sta scrivendo la tua storia..."):
                    try:
                        words = [c.get('german', '') for c in st.session_state.flashcards if 'german' in c]
                        random.shuffle(words)
                        selected_words = words[:20] # Usa fino a 20 parole del database
                        
                        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                        prompt = f"Scrivi un testo in tedesco (livello {level}) sul tema: '{topic}'. Cerca di includere il più possibile queste parole: {', '.join(selected_words)}. Restituisci SOLO il testo in tedesco, diviso in paragrafi chiari."
                        
                        response = model.generate_content(prompt)
                        st.session_state.current_story = response.text
                    except Exception as e:
                        st.error(f"Errore: {e}")
        
        # Se c'è una storia generata, mostrala e offri il dizionario
        if 'current_story' in st.session_state:
            st.markdown(f'<div class="reader-box">{st.session_state.current_story}</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("🔍 Dizionario Rapido")
            st.write("Hai trovato una parola difficile nel testo? Scrivila qui sotto per farti spiegare il significato nel contesto.")
            
            lookup_word = st.text_input("Parola da cercare:")
            if st.button("Traduci Parola"):
                if lookup_word.strip():
                    with st.spinner("Cerco nel dizionario AI..."):
                        try:
                            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                            prompt_dict = f"Nel contesto di questo testo: '{st.session_state.current_story[:500]}...', cosa significa la parola tedesca '{lookup_word}'? Spiega brevemente in italiano il significato e la grammatica."
                            resp_dict = model.generate_content(prompt_dict)
                            st.info(resp_dict.text)
                        except Exception as e:
                            st.error(f"Errore: {e}")

# --- VISTA: MODALITÀ STUDIO ---
elif menu == "🧠 Modalità Studio":
    st.title("🧠 Modalità Studio")
    
    if not st.session_state.flashcards:
        st.info("Aggiungi prima delle flashcard!")
    else:
        # FASE 1: SETUP
        if st.session_state.study_phase == "setup":
            st.markdown("### Scegli la tua sessione:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🎯 Selezione Manuale")
                st.write("Studia solo le card che hai spuntato nella Dashboard.")
                manual_count = sum(1 for c in st.session_state.flashcards if c.get('selected', False))
                st.write(f"Card selezionate: **{manual_count}**")
                
                if st.button("Inizia Manuale"):
                    if manual_count == 0:
                        st.warning("Non hai spuntato nessuna card! Vai nella Dashboard.")
                    else:
                        st.session_state.study_queue = [c for c in st.session_state.flashcards if c.get('selected', False)]
                        random.shuffle(st.session_state.study_queue)
                        st.session_state.study_idx = 0
                        st.session_state.card_flipped = False
                        st.session_state.session_errors = []
                        st.session_state.study_phase = "active"
                        st.rerun()
                        
            with col2:
                st.markdown("#### 🧠 Smart Random")
                st.write("L'algoritmo sceglie le parole che sbagli più spesso.")
                num_cards = st.number_input("Numero di card:", min_value=1, max_value=len(st.session_state.flashcards), value=min(15, len(st.session_state.flashcards)))
                
                if st.button("Inizia Smart"):
                    # Algoritmo: Percentuale di errore
                    def error_rate(c):
                        tot = int(c.get('correctCount', 0)) + int(c.get('incorrectCount', 0))
                        return int(c.get('incorrectCount', 0)) / tot if tot > 0 else 0.5
                    
                    sorted_cards = sorted(st.session_state.flashcards, key=error_rate, reverse=True)
                    st.session_state.study_queue = sorted_cards[:num_cards]
                    random.shuffle(st.session_state.study_queue) # Mischia le più difficili
                    st.session_state.study_idx = 0
                    st.session_state.card_flipped = False
                    st.session_state.session_errors = []
                    st.session_state.study_phase = "active"
                    st.rerun()

        # FASE 2: STUDIO ATTIVO
        elif st.session_state.study_phase == "active":
            if st.session_state.study_idx < len(st.session_state.study_queue):
                card = st.session_state.study_queue[st.session_state.study_idx]
                
                st.progress((st.session_state.study_idx) / len(st.session_state.study_queue))
                st.caption(f"Carta {st.session_state.study_idx + 1} di {len(st.session_state.study_queue)}")
                
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
                    
                    # Trova indice nel DB principale per salvare
                    db_idx = next((i for i, c in enumerate(st.session_state.flashcards) if c['id'] == card['id']), -1)
                    
                    with col1:
                        if st.button("❌ No, non la so"):
                            if db_idx != -1:
                                st.session_state.flashcards[db_idx]['incorrectCount'] = int(st.session_state.flashcards[db_idx].get('incorrectCount', 0)) + 1
                                save_data(st.session_state.flashcards)
                            st.session_state.session_errors.append(card)
                            st.session_state.study_idx += 1
                            st.session_state.card_flipped = False
                            st.rerun()
                            
                    with col2:
                        if st.button("✅ Sì, la so"):
                            if db_idx != -1:
                                st.session_state.flashcards[db_idx]['correctCount'] = int(st.session_state.flashcards[db_idx].get('correctCount', 0)) + 1
                                save_data(st.session_state.flashcards)
                            st.session_state.study_idx += 1
                            st.session_state.card_flipped = False
                            st.rerun()
            else:
                st.session_state.study_phase = "summary"
                st.rerun()

        # FASE 3: RIEPILOGO
        elif st.session_state.study_phase == "summary":
            st.balloons()
            st.markdown("<h2 style='text-align: center;'>Sessione Completata! 🎉</h2>", unsafe_allow_html=True)
            
            totali = len(st.session_state.study_queue)
            sbagliate = len(st.session_state.session_errors)
            corrette = totali - sbagliate
            
            col1, col2 = st.columns(2)
            col1.metric("✅ Corrette", corrette)
            col2.metric("❌ Da ripassare", sbagliate)
            
            st.markdown("---")
            
            if sbagliate > 0:
                if st.button("🔄 Ripeti solo gli errori"):
                    st.session_state.study_queue = st.session_state.session_errors.copy()
                    random.shuffle(st.session_state.study_queue)
                    st.session_state.study_idx = 0
                    st.session_state.card_flipped = False
                    st.session_state.session_errors = []
                    st.session_state.study_phase = "active"
                    st.rerun()
            
            if st.button("🏠 Torna alla Dashboard"):
                st.session_state.study_phase = "setup"
                st.rerun()
