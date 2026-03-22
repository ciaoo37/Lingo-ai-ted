import streamlit as st
import pandas as pd
import json
import os
import random
import google.generativeai as genai

# --- CONFIGURAZIONE PAGINA ---
# Usiamo layout="centered" perché su mobile e per le flashcard è molto più elegante
st.set_page_config(page_title="LingoAI - Tedesco", page_icon="🧠", layout="centered")

# --- CUSTOM CSS (Design Moderno) ---
st.markdown("""
<style>
    /* Sfondo generale dell'app più morbido */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Stile della Flashcard */
    .flashcard {
        background-color: #ffffff;
        border-radius: 24px;
        padding: 3rem 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 2rem auto;
        border: 1px solid #e2e8f0;
        max-width: 600px;
        transition: transform 0.3s ease;
    }
    
    .flashcard:hover {
        transform: translateY(-5px);
    }
    
    .fc-category {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #94a3b8;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .fc-german {
        font-size: 3.5rem;
        font-weight: 800;
        color: #4f46e5; /* Indaco moderno */
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    
    .fc-italian {
        font-size: 2rem;
        font-weight: 600;
        color: #334155;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 2px dashed #e2e8f0;
    }
    
    .fc-details {
        font-size: 1.2rem;
        color: #64748b;
        margin-top: 0.5rem;
    }
    
    .fc-example {
        margin-top: 1.5rem;
        padding: 1.2rem;
        background-color: #f1f5f9;
        border-radius: 16px;
        font-size: 1.1rem;
        color: #475569;
        font-style: italic;
    }
    
    /* Stile Bottoni Generali (Grandi e arrotondati) */
    div[data-testid="stButton"] button {
        border-radius: 16px;
        font-weight: 700;
        height: 3.5rem;
        font-size: 1.1rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        width: 100%;
    }
    
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Testo Reader */
    .reader-text {
        font-size: 1.3rem;
        line-height: 1.8;
        color: #1e293b;
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIONE DATI (Anti-Crash) ---
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

# Variabile di stato per capire se la carta è girata
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
    st.title("📊 Dashboard")
    
    if st.session_state.flashcards:
        # Metriche in stile moderno
        col1, col2, col3 = st.columns(3)
        tot_cards = len(st.session_state.flashcards)
        tot_correct = sum(c.get('correctCount', 0) for c in st.session_state.flashcards)
        tot_incorrect = sum(c.get('incorrectCount', 0) for c in st.session_state.flashcards)
        
        col1.metric("🃏 Flashcard Totali", tot_cards)
        col2.metric("✅ Risposte Esatte", tot_correct)
        col3.metric("❌ Errori", tot_incorrect)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        df = pd.DataFrame(st.session_state.flashcards)
        cols_to_show = [col for col in ['category', 'german', 'italian', 'correctCount', 'incorrectCount'] if col in df.columns]
        st.dataframe(df[cols_to_show], use_container_width=True)
        
        if st.button("🗑️ Elimina tutte le flashcard"):
            st.session_state.flashcards = []
            save_data([])
            st.rerun()
    else:
        st.info("👋 Benvenuto! Non hai ancora flashcard. Vai su 'Genera Flashcard' per iniziare.")

# --- VISTA: GENERA CON AI ---
elif menu == "✨ Genera Flashcard":
    st.title("✨ Genera con AI")
    
    if not api_key:
        st.warning("⚠️ Inserisci la tua API Key nella barra laterale per usare l'AI.")
    else:
        st.write("Incolla una lista di parole. L'AI troverà articoli, plurali e creerà frasi d'esempio.")
        words_input = st.text_area("Lista parole (una per riga):", height=150, placeholder="Es:\nHund\nKatze\nlaufen")
        
        if st.button("🚀 Genera Flashcard Magiche"):
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
                            "category": "Scegli tra: Verbi, Sostantivi, Aggettivi, Avverbi, Pronomi, Espressioni",
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
        col1, col2 = st.columns([1, 3])
        with col1:
            level = st.selectbox("Livello", ["A1", "A2", "B1", "B2"])
        
        if st.button("📚 Scrivi una storia per me"):
            with st.spinner("L'AI sta scrivendo..."):
                try:
                    words = [c.get('german', '') for c in st.session_state.flashcards if 'german' in c]
                    random.shuffle(words)
                    selected_words = words[:15]
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Scrivi un breve testo in tedesco (livello {level}) che includa il più possibile queste parole: {', '.join(selected_words)}. Restituisci SOLO il testo in tedesco, formattato in paragrafi."
                    
                    response = model.generate_content(prompt)
                    
                    # Mostra il testo dentro un div con stile personalizzato
                    st.markdown(f'<div class="reader-text">{response.text}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Errore: {e}")

# --- VISTA: MODALITÀ STUDIO ---
elif menu == "🧠 Modalità Studio":
    st.title("🧠 Modalità Studio")
    
    if not st.session_state.flashcards:
        st.info("Aggiungi prima delle flashcard nella sezione 'Genera Flashcard'!")
    else:
        # Setup della sessione
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
            
            # Estrai i dati in modo sicuro
            category = card.get('category', 'Generale')
            article = card.get('article', '')
            german = card.get('german', '')
            italian = card.get('italian', '')
            plural = card.get('plural', '')
            ex_de = card.get('exampleSentenceGerman', '')
            ex_it = card.get('exampleSentenceItalian', '')
            
            # Crea l'HTML della flashcard
            if not st.session_state.card_flipped:
                # FRONTE DELLA CARTA
                card_html = f"""
                <div class="flashcard">
                    <div class="fc-category">{category}</div>
                    <div class="fc-german">{article} {german}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Container centrato per il bottone
                _, col_btn, _ = st.columns([1, 2, 1])
                with col_btn:
                    if st.button("🔄 Gira la carta"):
                        st.session_state.card_flipped = True
                        st.rerun()
            
            else:
                # RETRO DELLA CARTA
                plural_html = f'<div class="fc-details"><b>Plurale:</b> {plural}</div>' if plural else ''
                example_html = f'<div class="fc-example">{ex_de}<br><span style="color:#94a3b8; font-size:0.9rem;">{ex_it}</span></div>' if ex_de else ''
                
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
                
                # Bottoni di risposta (Verde e Rosso)
                col1, col2 = st.columns(2)
                
                try:
                    original_index = st.session_state.flashcards.index(card)
                except ValueError:
                    original_index = -1
                
                with col1:
                    if st.button("❌ Non la so"):
                        if original_index != -1:
                            st.session_state.flashcards[original_index]['incorrectCount'] = st.session_state.flashcards[original_index].get('incorrectCount', 0) + 1
                            save_data(st.session_state.flashcards)
                        st.session_state.study_index += 1
                        st.session_state.card_flipped = False
                        st.rerun()
                        
                with col2:
                    if st.button("✅ La so"):
                        if original_index != -1:
                            st.session_state.flashcards[original_index]['correctCount'] = st.session_state.flashcards[original_index].get('correctCount', 0) + 1
                            save_data(st.session_state.flashcards)
                        st.session_state.study_index += 1
                        st.session_state.card_flipped = False
                        st.rerun()
                
        else:
            st.balloons()
            st.success("🎉 Hai completato la sessione di studio!")
            if st.button("🔄 Inizia una nuova sessione", use_container_width=True):
                del st.session_state.study_index
                st.session_state.card_flipped = False
                st.rerun()
