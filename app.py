import streamlit as st
import pandas as pd
import json
import os
import random
import google.generativeai as genai

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LingoAI - Tedesco", page_icon="🧠", layout="centered")

# --- CUSTOM CSS (Stile Moderno, Compatibile con Light/Dark Mode) ---
st.markdown("""
<style>
    /* Rimuove il padding eccessivo in alto su mobile */
    .block-container {
        padding-top: 2rem;
    }

    /* Stile della Flashcard */
    .flashcard {
        background-color: var(--secondary-background-color);
        border-radius: 32px;
        padding: 3rem 2rem;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.3);
        text-align: center;
        margin: 1rem auto 2rem auto;
        border: 1px solid rgba(128, 128, 128, 0.2);
        max-width: 500px;
    }
    
    .fc-category {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #8b5cf6; /* Viola acceso, visibile sia in light che dark */
        font-weight: 700;
        margin-bottom: 1.5rem;
    }
    
    .fc-german {
        font-size: 3.5rem;
        font-weight: 800;
        color: var(--text-color);
        line-height: 1.1;
        margin-bottom: 1rem;
    }
    
    .fc-italian {
        font-size: 2rem;
        font-weight: 600;
        color: #10b981; /* Verde smeraldo */
        margin-top: 2rem;
        padding-top: 2rem;
        border-top: 2px dashed rgba(128, 128, 128, 0.3);
    }
    
    .fc-details {
        font-size: 1.1rem;
        color: var(--text-color);
        opacity: 0.7;
        margin-top: 0.5rem;
    }
    
    .fc-example {
        margin-top: 2rem;
        padding: 1.5rem;
        background-color: rgba(128, 128, 128, 0.1);
        border-radius: 20px;
        font-size: 1.1rem;
        color: var(--text-color);
        font-style: italic;
    }

    /* Stile per le metriche della Dashboard */
    .dash-card {
        background-color: var(--secondary-background-color);
        border-radius: 24px;
        padding: 1.5rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
        display: flex;
        align-items: center;
        gap: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .dash-icon {
        font-size: 2.5rem;
        background: rgba(128, 128, 128, 0.1);
        padding: 1rem;
        border-radius: 20px;
    }
    .dash-text h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 800;
        color: var(--text-color);
    }
    .dash-text p {
        margin: 0;
        font-size: 0.8rem;
        text-transform: uppercase;
        font-weight: 700;
        color: var(--text-color);
        opacity: 0.5;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIONE DATI ---
DATA_FILE = "flashcards.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return []
            return json.loads(content)
    except Exception as e:
        st.sidebar.error(f"Errore database: {e}")
        return []

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Impossibile salvare i dati: {e}")

if 'flashcards' not in st.session_state:
    st.session_state.flashcards = load_data()

if 'card_flipped' not in st.session_state:
    st.session_state.card_flipped = False

# --- BARRA LATERALE ---
with st.sidebar:
    st.title("⚙️ Impostazioni")
    api_key = st.text_input("🔑 Google Gemini API Key", type="password")
    
    st.markdown("---")
    st.markdown("### 📍 Navigazione")
    menu = st.radio(
        "", 
        ["📊 Dashboard", "✨ Genera Flashcard", "📖 Smart Reader", "🧠 Modalità Studio"],
        label_visibility="collapsed"
    )

if api_key:
    genai.configure(api_key=api_key)

# --- VISTA: DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("Benvenuto! 👋")
    st.markdown("<p style='opacity: 0.7; margin-bottom: 2rem;'>Ecco il riepilogo del tuo studio di Tedesco.</p>", unsafe_allow_html=True)
    
    if st.session_state.flashcards:
        tot_cards = len(st.session_state.flashcards)
        tot_correct = sum(c.get('correctCount', 0) for c in st.session_state.flashcards)
        tot_incorrect = sum(c.get('incorrectCount', 0) for c in st.session_state.flashcards)
        
        # Dashboard Cards in HTML per un look moderno
        st.markdown(f"""
        <div class="dash-card">
            <div class="dash-icon">📚</div>
            <div class="dash-text">
                <p>Flashcard Totali</p>
                <h3>{tot_cards}</h3>
            </div>
        </div>
        <div class="dash-card">
            <div class="dash-icon" style="color: #10b981;">✅</div>
            <div class="dash-text">
                <p>Risposte Esatte</p>
                <h3>{tot_correct}</h3>
            </div>
        </div>
        <div class="dash-card">
            <div class="dash-icon" style="color: #f43f5e;">❌</div>
            <div class="dash-text">
                <p>Errori Totali</p>
                <h3>{tot_incorrect}</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 Le tue parole")
        df = pd.DataFrame(st.session_state.flashcards)
        cols_to_show = [col for col in ['category', 'german', 'italian', 'correctCount', 'incorrectCount'] if col in df.columns]
        st.dataframe(df[cols_to_show], use_container_width=True)
        
        if st.button("🗑️ Elimina tutte le flashcard", type="secondary"):
            st.session_state.flashcards = []
            save_data([])
            st.rerun()
    else:
        st.info("Non hai ancora flashcard. Vai su 'Genera Flashcard' per iniziare.")

# --- VISTA: GENERA CON AI ---
elif menu == "✨ Genera Flashcard":
    st.title("✨ Genera con AI")
    
    if not api_key:
        st.warning("⚠️ Inserisci la tua API Key nella barra laterale per usare l'AI.")
    else:
        st.markdown("<p style='opacity: 0.7;'>Incolla una lista di parole. L'AI troverà articoli, plurali e creerà frasi d'esempio.</p>", unsafe_allow_html=True)
        words_input = st.text_area("Lista parole (una per riga):", height=150, placeholder="Es:\nHund\nKatze\nlaufen")
        
        if st.button("🚀 Genera Flashcard Magiche", type="primary", use_container_width=True):
            if not words_input.strip():
                st.warning("Inserisci almeno una parola.")
            else:
                with st.spinner("L'AI sta creando le tue card..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"""
                        Genera flashcard in italiano e tedesco per queste parole:
                        {words_input}
                        
                        Restituisci ESATTAMENTE un array JSON valido.
                        Struttura per ogni parola:
                        {{
                            "category": "Sostantivi",
                            "german": "parola in tedesco",
                            "italian": "traduzione in italiano",
                            "article": "articolo determinativo se è un sostantivo, altrimenti vuoto",
                            "plural": "forma plurale se è un sostantivo, altrimenti vuoto",
                            "exampleSentenceGerman": "frase di esempio in tedesco",
                            "exampleSentenceItalian": "traduzione della frase in italiano",
                            "cloze": "la frase in tedesco con la parola bersaglio sostituita da '___'"
                        }}
                        """
                        response = model.generate_content(
                            prompt,
                            generation_config=genai.GenerationConfig(response_mime_type="application/json")
                        )
                        
                        new_cards = json.loads(response.text)
                        for card in new_cards:
                            card['correctCount'] = 0
                            card['incorrectCount'] = 0
                            
                        st.session_state.flashcards.extend(new_cards)
                        save_data(st.session_state.flashcards)
                        st.success(f"🎉 {len(new_cards)} flashcard aggiunte al tuo mazzo!")
                    except Exception as e:
                        st.error(f"Errore durante la generazione: {e}")

# --- VISTA: SMART READER ---
elif menu == "📖 Smart Reader":
    st.title("📖 Smart Reader")
    
    if not api_key:
        st.warning("⚠️ Inserisci la tua API Key nella barra laterale per usare l'AI.")
    elif not st.session_state.flashcards:
        st.info("Devi prima salvare qualche flashcard per generare un testo personalizzato.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            level = st.selectbox("Livello", ["A1", "A2", "B1", "B2"])
        
        if st.button("📚 Scrivi una storia per me", type="primary"):
            with st.spinner("L'AI sta scrivendo..."):
                try:
                    words = [c.get('german', '') for c in st.session_state.flashcards if 'german' in c]
                    random.shuffle(words)
                    selected_words = words[:15]
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Scrivi un breve testo in tedesco (livello {level}) che includa il più possibile queste parole: {', '.join(selected_words)}. Restituisci SOLO il testo in tedesco, formattato in paragrafi."
                    
                    response = model.generate_content(prompt)
                    
                    st.markdown("### Il tuo testo:")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Errore: {e}")

# --- VISTA: MODALITÀ STUDIO ---
elif menu == "🧠 Modalità Studio":
    st.title("🧠 Modalità Studio")
    
    if not st.session_state.flashcards:
        st.info("Aggiungi prima delle flashcard nella sezione 'Genera Flashcard'!")
    else:
        if 'study_index' not in st.session_state:
            st.session_state.study_index = 0
            st.session_state.card_flipped = False
            sorted_cards = sorted(st.session_state.flashcards, key=lambda x: x.get('incorrectCount', 0), reverse=True)
            st.session_state.study_cards = sorted_cards[:20]
        
        if st.session_state.study_index < len(st.session_state.study_cards):
            card = st.session_state.study_cards[st.session_state.study_index]
            
            # Progress bar
            progress = (st.session_state.study_index) / len(st.session_state.study_cards)
            st.progress(progress)
            st.caption(f"Carta {st.session_state.study_index + 1} di {len(st.session_state.study_cards)}")
            
            # Estrai i dati
            category = card.get('category', 'Generale')
            article = card.get('article', '')
            german = card.get('german', '')
            italian = card.get('italian', '')
            plural = card.get('plural', '')
            ex_de = card.get('exampleSentenceGerman', '')
            ex_it = card.get('exampleSentenceItalian', '')
            
            if not st.session_state.card_flipped:
                # FRONTE DELLA CARTA
                card_html = f"""
                <div class="flashcard">
                    <div class="fc-category">{category}</div>
                    <div class="fc-german">{article} {german}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Bottone per girare
                _, col_btn, _ = st.columns([1, 2, 1])
                with col_btn:
                    if st.button("🔄 Gira la carta", type="primary", use_container_width=True):
                        st.session_state.card_flipped = True
                        st.rerun()
            
            else:
                # RETRO DELLA CARTA
                plural_html = f'<div class="fc-details"><b>Plurale:</b> {plural}</div>' if plural else ''
                example_html = f'<div class="fc-example">{ex_de}<br><span style="opacity:0.7; font-size:0.9rem;">{ex_it}</span></div>' if ex_de else ''
                
                card_html = f"""
                <div class="flashcard">
                    <div class="fc-category">{category}</div>
                    <div class="fc-german">{article} {german}</div>
                    <div class="fc-italian">🇮🇹 {italian}</div>
                    {plural_html}
                    {example_html}
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Bottoni Rosso e Verde
                col1, col2 = st.columns(2)
                
                try:
                    original_index = st.session_state.flashcards.index(card)
                except ValueError:
                    original_index = -1
                
                with col1:
                    if st.button("❌ Non la so", use_container_width=True):
                        if original_index != -1:
                            st.session_state.flashcards[original_index]['incorrectCount'] = st.session_state.flashcards[original_index].get('incorrectCount', 0) + 1
                            save_data(st.session_state.flashcards)
                        st.session_state.study_index += 1
                        st.session_state.card_flipped = False
                        st.rerun()
                        
                with col2:
                    if st.button("✅ La so", use_container_width=True):
                        if original_index != -1:
                            st.session_state.flashcards[original_index]['correctCount'] = st.session_state.flashcards[original_index].get('correctCount', 0) + 1
                            save_data(st.session_state.flashcards)
                        st.session_state.study_index += 1
                        st.session_state.card_flipped = False
                        st.rerun()
                
        else:
            st.balloons()
            st.success("🎉 Hai completato la sessione di studio!")
            if st.button("🔄 Inizia una nuova sessione", type="primary", use_container_width=True):
                del st.session_state.study_index
                st.session_state.card_flipped = False
                st.rerun()
