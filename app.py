import streamlit as st
import pandas as pd
import os
import json
import google.generativeai as genai

# --- 1. CONFIGURAZIONE PAGINA E DESIGN ---
st.set_page_config(page_title="SprachMaster: Deutsch-Italienisch", layout="wide", initial_sidebar_state="expanded")

# CSS Personalizzato: Times New Roman, Colori Professionali, Mobile-First, Nessuna Emoji
st.markdown("""
<style>
    /* Tipografia: Times New Roman ovunque */
    html, body, [class*="css"], p, h1, h2, h3, h4, h5, h6, span, div, button, input, select, textarea {
        font-family: 'Times New Roman', Times, serif !important;
    }
    
    /* Stile Bottoni Mobile-First */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        padding: 15px !important;
        font-size: 18px !important;
        border: 1px solid #0055ff !important;
    }
    
    /* Colore Primario: Blu */
    button[kind="primary"] {
        background-color: #0055ff !important;
        color: white !important;
    }
    
    /* Pulsante Rosso (Non la so) */
    button:has(div:contains("Non la so")) {
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
        color: white !important;
    }
    
    /* Pulsante Verde (La so) */
    button:has(div:contains("La so")) {
        background-color: #4caf50 !important;
        border-color: #4caf50 !important;
        color: white !important;
    }
    
    /* Stile Card */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
        background-color: rgba(0, 85, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Centrare i testi */
    .centered-text {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTIONE DATABASE (CSV) ---
CSV_FILE = "flashcards.csv"
COLUMNS = ["Termine", "Articolo_Plurale", "Traduzione", "Categoria", "Esempio", "Errori", "Successi", "Selezionata"]

def load_data():
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(CSV_FILE, index=False)
        return df
    return pd.read_csv(CSV_FILE)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- 3. GESTIONE API KEY E NAVIGAZIONE ---
with st.sidebar:
    st.header("Impostazioni AI")
    # Campo per inserire la chiave API come richiesto
    api_key_input = st.text_input("Inserisci la tua Google API Key", type="password")
    
    if api_key_input:
        genai.configure(api_key=api_key_input)
        st.success("Chiave API configurata.")
    else:
        st.warning("Inserisci la chiave nella barra laterale per attivare l'IA.")
        
    st.markdown("---")
    st.header("Navigazione")
    menu = ["Dashboard", "Genera Flashcard", "Smart Reader", "Studio"]
    choice = st.radio("Seleziona Sezione", menu)

# --- FUNZIONE HELPER PER IL MODELLO AI ---
def get_ai_model():
    """Restituisce il modello configurato esattamente come richiesto per evitare l'errore 404."""
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"fallback_to_older_models": True}
    )

# --- 4. SEZIONE: DASHBOARD ---
if choice == "Dashboard":
    st.title("Dashboard Flashcard")
    df = load_data()
    
    if df.empty:
        st.info("Nessuna flashcard presente. Vai alla sezione 'Genera Flashcard' per aggiungerne.")
    else:
        # Barra Filtro
        st.subheader("Filtra e Seleziona")
        categories = ["Tutte"] + sorted(df["Categoria"].dropna().unique().tolist())
        selected_category = st.radio("Filtra per Categoria", categories, horizontal=True)
        
        if selected_category != "Tutte":
            mask = df["Categoria"] == selected_category
        else:
            mask = pd.Series(True, index=df.index)
            
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            if st.button("Seleziona tutto il filtrato", type="primary"):
                df.loc[mask, "Selezionata"] = True
                save_data(df)
                st.rerun()
        with col_sel2:
            if st.button("Deseleziona tutto il filtrato"):
                df.loc[mask, "Selezionata"] = False
                save_data(df)
                st.rerun()
                
        # Tabella di Controllo Manuale
        st.subheader("Catalogo Flashcard")
        edited_df = st.data_editor(
            df[mask],
            column_config={
                "Selezionata": st.column_config.CheckboxColumn("Selezionata"),
            },
            disabled=["Termine", "Articolo_Plurale", "Traduzione", "Categoria", "Esempio", "Errori", "Successi"],
            hide_index=True,
            use_container_width=True,
            key="data_editor"
        )
        
        if not edited_df.equals(df[mask]):
            df.loc[mask, "Selezionata"] = edited_df["Selezionata"].values
            save_data(df)
            
        # Modifica e Eliminazione Singola (Nessun tasto "Elimina tutto")
        st.markdown("---")
        st.subheader("Azioni Manuali")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            word_to_edit = st.selectbox("Parola da modificare", df[mask]["Termine"].tolist(), key="edit_select")
            if st.button("[Modifica] Apri modulo"):
                st.session_state['edit_word'] = word_to_edit
                st.rerun()
        with col_act2:
            word_to_delete = st.selectbox("Parola da eliminare", df[mask]["Termine"].tolist(), key="del_select")
            if st.button("[Elimina] Rimuovi singola parola"):
                df = df[df["Termine"] != word_to_delete]
                save_data(df)
                st.success("Parola eliminata con successo.")
                st.rerun()
                
        # Modulo di Modifica
        if 'edit_word' in st.session_state and st.session_state['edit_word']:
            st.markdown("### Modulo Modifica")
            word = st.session_state['edit_word']
            if word in df["Termine"].values:
                row = df[df["Termine"] == word].iloc[0]
                with st.form("edit_form"):
                    new_termine = st.text_input("Termine", row["Termine"])
                    new_art_plur = st.text_input("Articolo e Plurale", row["Articolo_Plurale"])
                    new_trad = st.text_input("Traduzione", row["Traduzione"])
                    new_cat = st.text_input("Categoria", row["Categoria"])
                    new_es = st.text_area("Esempio", row["Esempio"])
                    if st.form_submit_button("Salva Modifiche"):
                        idx = df[df["Termine"] == word].index[0]
                        df.at[idx, "Termine"] = new_termine
                        df.at[idx, "Articolo_Plurale"] = new_art_plur
                        df.at[idx, "Traduzione"] = new_trad
                        df.at[idx, "Categoria"] = new_cat
                        df.at[idx, "Esempio"] = new_es
                        save_data(df)
                        st.session_state['edit_word'] = None
                        st.success("Modifiche salvate!")
                        st.rerun()

# --- 5. SEZIONE: GENERA FLASHCARD ---
elif choice == "Genera Flashcard":
    st.title("Genera Flashcard con AI")
    st.write("Incolla una lista di parole (una per riga). L'AI completerà automaticamente i dati.")
    
    words_input = st.text_area("Lista parole", height=200)
    
    if st.button("Genera Flashcard", type="primary"):
        if not api_key_input:
            st.error("Inserisci la API Key nella barra laterale per procedere.")
        elif not words_input.strip():
            st.warning("Inserisci almeno una parola.")
        else:
            words_list = [w.strip() for w in words_input.split('\n') if w.strip()]
            
            prompt = f"""
            Analizza la seguente lista di parole in tedesco o italiano:
            {words_list}
            
            Per ogni parola, fornisci un output JSON strutturato come una lista di oggetti con le seguenti chiavi esatte:
            - "Termine": La parola originale in tedesco.
            - "Articolo_Plurale": L'articolo determinativo e la forma plurale (solo se è un sostantivo, altrimenti stringa vuota).
            - "Traduzione": La traduzione in italiano.
            - "Categoria": La classificazione grammaticale (es. Verbo, Sostantivo, Aggettivo).
            - "Esempio": Una frase d'esempio naturale in tedesco.
            
            Restituisci SOLO codice JSON valido, senza formattazione markdown aggiuntiva.
            """
            
            with st.spinner("Generazione in corso..."):
                try:
                    model = get_ai_model()
                    response = model.generate_content(prompt)
                    
                    text = response.text.strip()
                    if text.startswith("```json"):
                        text = text[7:-3]
                    elif text.startswith("```"):
                        text = text[3:-3]
                        
                    data = json.loads(text.strip())
                    st.session_state['generated_cards'] = data
                    st.success("Generazione completata! Rivedi i risultati qui sotto.")
                except Exception as e:
                    st.error("Si è verificato un errore di rete o di configurazione con l'Intelligenza Artificiale. Verifica che la tua API Key sia corretta, che non ci siano spazi vuoti accidentali e di avere una connessione internet stabile. Riprova tra qualche istante.")

    if 'generated_cards' in st.session_state:
        st.subheader("Revisione Risultati")
        gen_df = pd.DataFrame(st.session_state['generated_cards'])
        edited_gen_df = st.data_editor(gen_df, use_container_width=True)
        
        if st.button("Salva nel Database", type="primary"):
            df = load_data()
            edited_gen_df["Errori"] = 0
            edited_gen_df["Successi"] = 0
            edited_gen_df["Selezionata"] = False
            
            df = pd.concat([df, edited_gen_df], ignore_index=True)
            save_data(df)
            del st.session_state['generated_cards']
            st.success("Flashcard salvate con successo!")

# --- 6. SEZIONE: SMART READER ---
elif choice == "Smart Reader":
    st.title("Smart Reader")
    st.write("Genera testi personalizzati basati sul tuo vocabolario.")
    
    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("Livello di difficoltà", ["A1", "A2", "B1", "B2"])
    with col2:
        theme = st.text_input("Tema della lettura (es. in aeroporto)")
        
    if st.button("Genera Testo", type="primary"):
        if not api_key_input:
            st.error("Inserisci la API Key nella barra laterale per procedere.")
        elif not theme:
            st.warning("Inserisci un tema.")
        else:
            df = load_data()
            vocab = df["Termine"].tolist()
            vocab_str = ", ".join(vocab[:50]) 
            
            prompt = f"""
            Scrivi un testo in tedesco di livello {level} sul tema: "{theme}".
            Cerca di utilizzare il più possibile le seguenti parole (se pertinenti al tema): {vocab_str}.
            Il testo deve essere naturale e grammaticalmente corretto.
            Restituisci solo il testo in tedesco, senza introduzioni.
            """
            
            with st.spinner("Generazione testo in corso..."):
                try:
                    model = get_ai_model()
                    response = model.generate_content(prompt)
                    st.session_state['reader_text'] = response.text
                except Exception as e:
                    st.error("Impossibile generare il testo. Verifica la tua API Key e la connessione internet, quindi riprova.")
                    
    if 'reader_text' in st.session_state:
        st.markdown("### Testo Generato")
        st.info(st.session_state['reader_text'])
        
        st.markdown("---")
        st.subheader("Traduzione Contestuale")
        word_to_translate = st.text_input("Inserisci una parola dal testo che non conosci:")
        if st.button("Traduci e Spiega"):
            if word_to_translate:
                prompt_trans = f"""
                Traduci la parola tedesca "{word_to_translate}" in italiano.
