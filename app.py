import streamlit as st
import pandas as pd
import json
import os
import random
import google.generativeai as genai

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LingoAI - Tedesco", page_icon="🧠", layout="wide")

# --- GESTIONE DATI ---
DATA_FILE = "flashcards.json"

def load_data():
    # Se il file non esiste, restituisci una lista vuota
    if not os.path.exists(DATA_FILE):
        return []
    
    # Prova a leggere il file. Se è corrotto o vuoto, restituisci una lista vuota
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return []
            return json.loads(content)
    except Exception as e:
        st.sidebar.error(f"Errore nella lettura del database: {e}")
        return []

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Impossibile salvare i dati: {e}")

# Inizializza il database in session_state se non esiste
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = load_data()

# --- BARRA LATERALE ---
st.sidebar.title("⚙️ Impostazioni")
api_key = st.sidebar.text_input("Inserisci la tua Google Gemini API Key", type="password")

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Menu Principale", 
    ["📚 Dashboard", "✨ Genera con AI", "📖 Smart Reader", "🧠 Modalità Studio"]
)

# Configura l'API di Google se la chiave è presente
if api_key:
    genai.configure(api_key=api_key)

# --- VISTA: DASHBOARD ---
if menu == "📚 Dashboard":
    st.title("📚 Dashboard e Gestione Flashcard")
    
    if st.session_state.flashcards:
        st.write(f"Hai salvato **{len(st.session_state.flashcards)}** flashcard in totale.")
        df = pd.DataFrame(st.session_state.flashcards)
        
        # Assicuriamoci che le colonne esistano prima di mostrarle per evitare errori
        cols_to_show = []
        for col in ['category', 'german', 'italian', 'correctCount', 'incorrectCount']:
            if col in df.columns:
                cols_to_show.append(col)
                
        st.dataframe(df[cols_to_show], use_container_width=True)
        
        # Opzione per eliminare tutto (per sicurezza)
        if st.button("🗑️ Elimina tutte le flashcard"):
            st.session_state.flashcards = []
            save_data([])
            st.rerun()
    else:
        st.info("Nessuna flashcard salvata. Vai nella sezione 'Genera con AI' per iniziare!")

# --- VISTA: GENERA CON AI ---
elif menu == "✨ Genera con AI":
    st.title("✨ Genera Flashcard con AI")
    
    if not api_key:
        st.warning("⚠️ Per favore, inserisci la tua API Key nella barra laterale per iniziare.")
    else:
        st.write("Incolla una lista di parole in tedesco o italiano. L'AI creerà le flashcard complete.")
        words_input = st.text_area("Lista parole (una per riga):", height=150)
        
        if st.button("Genera Flashcard"):
            if not words_input.strip():
                st.warning("Inserisci almeno una parola.")
            else:
                with st.spinner("L'AI sta lavorando... attendi qualche secondo."):
                    try:
                        # Usiamo il modello stabile 1.5-flash
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = f"""
                        Genera flashcard in italiano e tedesco per queste parole:
                        {words_input}
                        
                        Devi restituire ESATTAMENTE un array JSON valido. Nessun altro testo.
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
                        
                        # Richiediamo esplicitamente JSON
                        response = model.generate_content(
                            prompt,
                            generation_config=genai.GenerationConfig(
                                response_mime_type="application/json"
                            )
                        )
                        
                        # Parsing del JSON
                        new_cards = json.loads(response.text)
                        
                        # Aggiungiamo i contatori
                        for card in new_cards:
                            card['correctCount'] = 0
                            card['incorrectCount'] = 0
                            
                        # Salviamo nel database
                        st.session_state.flashcards.extend(new_cards)
                        save_data(st.session_state.flashcards)
                        st.success(f"🎉 {len(new_cards)} flashcard generate e salvate con successo!")
                        
                    except Exception as e:
                        st.error(f"Si è verificato un errore durante la generazione: {e}")
                        st.info("Assicurati che la lista di parole sia chiara e riprova.")

# --- VISTA: SMART READER ---
elif menu == "📖 Smart Reader":
    st.title("📖 Smart Reader")
    
    if not api_key:
        st.warning("⚠️ Per favore, inserisci la tua API Key nella barra laterale per iniziare.")
    elif not st.session_state.flashcards:
        st.info("Devi prima salvare qualche flashcard per generare un testo personalizzato.")
    else:
        st.write("Leggi brevi testi generati usando le parole che stai studiando.")
        level = st.selectbox("Scegli il livello di difficoltà", ["A1", "A2", "B1", "B2"])
        
        if st.button("Genera Testo"):
            with st.spinner("Scrittura in corso..."):
                try:
                    # Prendi fino a 15 parole a caso dal database
                    words = [c.get('german', '') for c in st.session_state.flashcards if 'german' in c]
                    random.shuffle(words)
                    selected_words = words[:15]
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Scrivi un breve testo in tedesco (livello {level}) che includa il più possibile queste parole: {', '.join(selected_words)}. Restituisci SOLO il testo in tedesco, senza traduzioni o note."
                    
                    response = model.generate_content(prompt)
                    
                    st.markdown("### Il tuo testo:")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Errore durante la generazione del testo: {e}")

# --- VISTA: MODALITÀ STUDIO ---
elif menu == "🧠 Modalità Studio":
    st.title("🧠 Modalità Studio (Swipe)")
    
    if not st.session_state.flashcards:
        st.info("Aggiungi prima delle flashcard nella sezione 'Genera con AI'!")
    else:
        # Inizializza la sessione di studio
        if 'study_index' not in st.session_state:
            st.session_state.study_index = 0
            # Ordina per numero di errori (decrescente) e prendi le prime 20
            sorted_cards = sorted(st.session_state.flashcards, key=lambda x: x.get('incorrectCount', 0), reverse=True)
            st.session_state.study_cards = sorted_cards[:20]
        
        # Se ci sono ancora carte da studiare nella sessione attuale
        if st.session_state.study_index < len(st.session_state.study_cards):
            card = st.session_state.study_cards[st.session_state.study_index]
            
            st.write(f"**Carta {st.session_state.study_index + 1} di {len(st.session_state.study_cards)}**")
            
            # Mostra la parola in tedesco
            st.markdown("---")
            article = card.get('article', '')
            german_word = card.get('german', 'Parola mancante')
            st.markdown(f"<h1 style='text-align: center; color: #4F46E5;'>{article} {german_word}</h1>", unsafe_allow_html=True)
            st.markdown("---")
            
            # Bottone per girare la carta
            if st.button("🔄 Gira la carta (Mostra Traduzione)", use_container_width=True):
                st.success(f"**Italiano:** {card.get('italian', '')}")
                
                if card.get('plural'):
                    st.write(f"**Plurale:** {card.get('plural')}")
                
                if card.get('exampleSentenceGerman'):
                    st.write(f"**Esempio:** {card.get('exampleSentenceGerman')}")
                    st.write(f"_{card.get('exampleSentenceItalian', '')}_")
            
            st.write("")
            col1, col2 = st.columns(2)
            
            # Troviamo l'indice originale della carta per aggiornare le statistiche
            try:
                original_index = st.session_state.flashcards.index(card)
            except ValueError:
                original_index = -1
            
            if col1.button("❌ Non la so", use_container_width=True):
                if original_index != -1:
                    st.session_state.flashcards[original_index]['incorrectCount'] = st.session_state.flashcards[original_index].get('incorrectCount', 0) + 1
                    save_data(st.session_state.flashcards)
                st.session_state.study_index += 1
                st.rerun()
                
            if col2.button("✅ La so", use_container_width=True):
                if original_index != -1:
                    st.session_state.flashcards[original_index]['correctCount'] = st.session_state.flashcards[original_index].get('correctCount', 0) + 1
                    save_data(st.session_state.flashcards)
                st.session_state.study_index += 1
                st.rerun()
                
        else:
            st.success("🎉 Hai completato la sessione di studio!")
            if st.button("Inizia una nuova sessione", use_container_width=True):
                del st.session_state.study_index
                st.rerun()
