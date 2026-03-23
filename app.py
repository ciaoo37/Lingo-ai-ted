import streamlit as st
import pandas as pd
import json
import os
import random
import google.generativeai as genai

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LingoAI - Tedesco", page_icon="🇩🇪", layout="centered")

# --- CUSTOM CSS (Design Moderno, Mobile First, Colori Personalizzati) ---
st.markdown("""
<style>
    /* Font Sans Serif elegante e sfondo grigio chiaro per far risaltare le card bianche */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #f3f4f6; /* Grigio chiarissimo */
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
        color: #dc2626; /* Rosso bandiera tedesca */
        font-weight: 800;
        margin-bottom: 1rem;
    }
    
    .fc-german {
        font-size: 3rem;
        font-weight: 800;
        color: #000000; /* Nero bandiera tedesca */
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
        border-left: 4px solid #dc2626; /* Dettaglio rosso */
    }

    /* Stile Bottoni Grandi e Colorati */
    div[data-testid="stButton"] button {
        border-radius: 20px;
        font-weight: 800;
        height: 4rem;
        font-size: 1.2rem;
        width: 100%;
        transition: transform 0.1s;
    }
    
    div[data-testid="stButton"] button:active {
        transform: scale(0.95);
    }

    /* Colora i bottoni in base all'emoji che contengono! */
    button:has(p:contains("✅")) {
        background-color: #10b981 !important; /* Verde smeraldo */
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
    }
    
    button:has(p:contains("❌")) {
        background-color: #ef4444 !important; /* Rosso acceso */
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4) !important;
    }
    
    button:has(p:contains("🔄")) {
        background-color: #1f2937 !important; /* Grigio scuro/Nero */
        color: white !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIONE DATI (CSV) ---
DATA_FILE = "flashcards.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        # Legge il CSV e sostituisce i valori vuoti (NaN) con stringhe vuote
        df = pd.read_csv(DATA_FILE)
        df = df.fillna("")
        return df.to_dict('records')
    except Exception as e:
        st.sidebar.error(f"Errore nella lettura del CSV: {e}")
        return []

def save_data(data):
    try:
        if not data:
            # Se la lista è vuota, crea un CSV vuoto
            pd.DataFrame().to_csv(DATA_FILE, index=False)
        else:
            # Salva la lista di dizionari in CSV
            pd.DataFrame(data).to_csv(DATA_FILE, index=False)
    except Exception as e:
        st.error(f"Impossibile salvare i dati nel CSV: {e}")

# Inizializza i dati
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = load_data()

if 'card_flipped' not in st.session_state:
    st.session_state.card_flipped = False

# --- BARRA LATERALE ---
with st.sidebar:
    st.title("⚙️ Impostazioni")
    api_key = st.text_input("🔑 Inserisci API Key", type="password", help="La tua chiave di Google Gemini")
    
    st.markdown("---")
    menu = st.radio(
        "📍 Navigazione", 
        ["📊 Dashboard", "✨ Genera Flashcard", "📖 Smart Reader", "🧠 Modalità Studio"]
    )

if api_key:
    genai.configure(api_key=api_key)

# --- VISTA: DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    if st.session_state.flashcards:
        tot_cards = len(st.session_state.flashcards)
        st.success(f"Hai **{tot_cards}** flashcard nel tuo database CSV.")
        
        st.markdown("### 📋 Le tue Parole (Mobile Friendly)")
        # Invece di una tabella, usiamo degli "expander" perfetti per il cellulare
        for i, card in enumerate(reversed(st.session_state.flashcards)):
            if i >= 15: # Mostra solo le ultime 15 per non appesantire il telefono
                st.write("*...e altre ancora!*")
                break
                
            titolo = f"{card.get('article', '')} {card.get('german', '')} ➔ {card.get('italian', '')}"
            with st.expander(titolo):
                st.write(f"**Categoria:** {card.get('category', '')}")
                st.write(f"**Plurale:** {card.get('plural', '-')}")
                st.write(f"**Risposte Esatte:** ✅ {card.get('correctCount', 0)}")
                st.write(f"**Errori:** ❌ {card.get('incorrectCount', 0)}")
        
        st.markdown("---")
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
        st.warning("⚠️ Per favore, inserisci la tua API Key nella barra laterale per iniziare.")
    else:
        st.write("Incolla una lista di parole. L'AI troverà articoli, plurali e creerà frasi d'esempio.")
        words_input = st.text_area("Lista parole (una per riga):", height=150, placeholder="Es:\nHund\nKatze\nlaufen")
        
        if st.button("🚀 Genera Flashcard"):
            if not words_input.strip():
                st.warning("Inserisci almeno una parola.")
            else:
                with st.spinner("L'AI sta creando le tue card..."):
                    try:
                        # Usiamo il NUOVO modello aggiornato
                        model = genai.GenerativeModel('gemini-2.5-flash')
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
                        
                        # Pulizia del testo nel caso Gemini aggiunga i backtick del markdown
                        testo_json = response.text.strip()
                        if testo_json.startswith("```json"):
                            testo_json = testo_json[7:-3]
                            
                        new_cards = json.loads(testo_json.strip())
                        
                        for card in new_cards:
                            card['correctCount'] = 0
                            card['incorrectCount'] = 0
                            
                        st.session_state.flashcards.extend(new_cards)
                        save_data(st.session_state.flashcards) # Salva nel CSV!
                        st.success(f"🎉 {len(new_cards)} flashcard aggiunte al tuo mazzo!")
                    except Exception as e:
                        st.error(f"Errore durante la generazione: {e}")

# --- VISTA: SMART READER ---
elif menu == "📖 Smart Reader":
    st.title("📖 Smart Reader")
    
    if not api_key:
        st.warning("⚠️ Per favore, inserisci la tua API Key nella barra laterale per iniziare.")
    elif not st.session_state.flashcards:
        st.info("Devi prima salvare qualche flashcard per generare un testo personalizzato.")
    else:
        level = st.selectbox("Scegli il livello", ["A1", "A2", "B1", "B2"])
        
        if st.button("📚 Scrivi una storia per me"):
            with st.spinner("L'AI sta scrivendo..."):
                try:
                    words = [c.get('german', '') for c in st.session_state.flashcards if 'german' in c]
                    random.shuffle(words)
                    selected_words = words[:15]
                    
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = f"Scrivi un breve testo in tedesco (livello {level}) che includa il più possibile queste parole: {', '.join(selected_words)}. Restituisci SOLO il testo in tedesco, formattato in paragrafi."
                    
                    response = model.generate_content(prompt)
                    
                    st.markdown(f"""
                    <div style="background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); font-size: 1.2rem; line-height: 1.6;">
                        {response.text}
                    </div>
                    """, unsafe_allow_html=True)
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
            sorted_cards = sorted(st.session_state.flashcards, key=lambda x: int(x.get('incorrectCount', 0)), reverse=True)
            st.session_state.study_cards = sorted_cards[:20]
        
        if st.session_state.study_index < len(st.session_state.study_cards):
            card = st.session_state.study_cards[st.session_state.study_index]
            
            st.caption(f"Carta {st.session_state.study_index + 1} di {len(st.session_state.study_cards)}")
            
            category = card.get('category', 'Generale')
            article = card.get('article', '')
            german = card.get('german', '')
            italian = card.get('italian', '')
            plural = card.get('plural', '')
            ex_de = card.get('exampleSentenceGerman', '')
            ex_it = card.get('exampleSentenceItalian', '')
            
            if not st.session_state.card_flipped:
                # FRONTE
                card_html = f"""
                <div class="flashcard">
                    <div class="fc-category">{category}</div>
                    <div class="fc-german">{article} {german}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                if st.button("🔄 Gira la carta"):
                    st.session_state.card_flipped = True
                    st.rerun()
            
            else:
                # RETRO
                plural_html = f'<div class="fc-details"><b>Plurale:</b> {plural}</div>' if plural else ''
                example_html = f'<div class="fc-example">🇩🇪 {ex_de}<br><br>🇮🇹 <span style="opacity:0.8;">{ex_it}</span></div>' if ex_de else ''
                
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
                
                # Bottoni Giganti Verde e Rosso
                col1, col2 = st.columns(2)
                
                try:
                    original_index = st.session_state.flashcards.index(card)
                except ValueError:
                    original_index = -1
                
                with col1:
                    if st.button("❌ Non la so"):
                        if original_index != -1:
                            st.session_state.flashcards[original_index]['incorrectCount'] = int(st.session_state.flashcards[original_index].get('incorrectCount', 0)) + 1
                            save_data(st.session_state.flashcards)
                        st.session_state.study_index += 1
                        st.session_state.card_flipped = False
                        st.rerun()
                        
                with col2:
                    if st.button("✅ La so"):
                        if original_index != -1:
                            st.session_state.flashcards[original_index]['correctCount'] = int(st.session_state.flashcards[original_index].get('correctCount', 0)) + 1
                            save_data(st.session_state.flashcards)
                        st.session_state.study_index += 1
                        st.session_state.card_flipped = False
                        st.rerun()
                
        else:
            st.balloons()
            st.success("🎉 Hai completato la sessione di studio!")
            if st.button("🔄 Inizia una nuova sessione"):
                del st.session_state.study_index
                st.session_state.card_flipped = False
                st.rerun()
