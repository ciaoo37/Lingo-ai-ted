import streamlit as st
import pandas as pd
import os
import json
import google.generativeai as genai

# --- 1. CONFIGURAZIONE PAGINA E DESIGN ---
# Impostiamo il layout largo e il titolo
st.set_page_config(page_title="SprachMaster: Deutsch-Italienisch", layout="wide", initial_sidebar_state="expanded")

# Inseriamo il CSS personalizzato per rispettare le tue regole di design
st.markdown("""
<style>
    /* Tipografia: Forza l'uso del Times New Roman ovunque */
    html, body, [class*="css"], p, h1, h2, h3, h4, h5, h6, span, div, button, input, select, textarea {
        font-family: 'Times New Roman', Times, serif !important;
    }
    
    /* Stile Bottoni Mobile-First: grandi, arrotondati e facili da cliccare */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        padding: 15px !important;
        font-size: 18px !important;
        border: 1px solid #0055ff !important;
    }
    
    /* Colore Primario: Blu per i bottoni principali */
    button[kind="primary"] {
        background-color: #0055ff !important;
        color: white !important;
    }
    
    /* Pulsante Rosso per gli errori ("Non la so") */
    button:has(div:contains("Non la so")) {
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
        color: white !important;
    }
    
    /* Pulsante Verde per i successi ("La so") */
    button:has(div:contains("La so")) {
        background-color: #4caf50 !important;
        border-color: #4caf50 !important;
        color: white !important;
    }
    
    /* Stile Card per i contenitori: bordi arrotondati e ombra leggera */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
        background-color: rgba(0, 85, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Classe per centrare i testi principali nelle flashcard */
    .centered-text {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTIONE DATABASE (CSV) ---
CSV_FILE = "flashcards.csv"
COLUMNS = ["Termine", "Articolo_Plurale", "Traduzione", "Categoria", "Esempio", "Errori", "Successi", "Selezionata"]

def load_data():
    """Carica i dati dal file CSV. Se non esiste, lo crea con le colonne corrette."""
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(CSV_FILE, index=False)
        return df
    return pd.read_csv(CSV_FILE)

def save_data(df):
    """Salva le modifiche nel file CSV."""
    df.to_csv(CSV_FILE, index=False)

# --- 3. CONFIGURAZIONE INTELLIGENZA ARTIFICIALE ---
# Cerchiamo la chiave API nelle variabili di ambiente (se presente)
api_key = os.environ.get("GEMINI_API_KEY")

# Creiamo la barra laterale per la navigazione e le impostazioni
with st.sidebar:
    st.header("Impostazioni AI")
    # Campo per inserire la chiave API se non è già configurata
    user_api_key = st.text_input("Inserisci Gemini API Key", type="password", value=api_key if api_key else "")
    if user_api_key:
        genai.configure(api_key=user_api_key)
    else:
        st.warning("API Key necessaria per le funzioni AI.")
        
    st.markdown("---")
    st.header("Navigazione")
    # Menu di navigazione principale
    menu = ["Dashboard", "Genera Flashcard (AI)", "Smart Reader", "Studio"]
    choice = st.radio("Seleziona Sezione", menu)

# --- 4. SEZIONE: DASHBOARD ---
if choice == "Dashboard":
    st.title("Dashboard Flashcard")
    df = load_data()
    
    if df.empty:
        st.info("Nessuna flashcard presente. Vai alla sezione 'Genera Flashcard (AI)' per aggiungerne.")
    else:
        # Barra Filtro Categorie
        st.subheader("Filtra e Seleziona")
        categories = ["Tutte"] + sorted(df["Categoria"].dropna().unique().tolist())
        selected_category = st.radio("Filtra per Categoria", categories, horizontal=True)
        
        # Applica il filtro
        if selected_category != "Tutte":
            mask = df["Categoria"] == selected_category
        else:
            mask = pd.Series(True, index=df.index)
            
        # Pulsanti per selezione massiva
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            if st.button("Seleziona tutte le visualizzate", type="primary"):
                df.loc[mask, "Selezionata"] = True
                save_data(df)
                st.rerun()
        with col_sel2:
            if st.button("Deseleziona tutte le visualizzate"):
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
            # Blocchiamo la modifica diretta in tabella per usare i moduli sicuri
            disabled=["Termine", "Articolo_Plurale", "Traduzione", "Categoria", "Esempio", "Errori", "Successi"],
            hide_index=True,
            use_container_width=True,
            key="data_editor"
        )
        
        # Sincronizza i checkbox cliccati nella tabella con il database
        if not edited_df.equals(df[mask]):
            df.loc[mask, "Selezionata"] = edited_df["Selezionata"].values
            save_data(df)
            
        # Modifica e Eliminazione Singola (senza emoji)
        st.markdown("---")
        st.subheader("Azioni Manuali")
        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            word_to_edit = st.selectbox("Parola da modificare", df[mask]["Termine"].tolist(), key="edit_select")
            if st.button("Modifica"):
                st.session_state['edit_word'] = word_to_edit
                st.rerun()
                
        with col_act2:
            word_to_delete = st.selectbox("Parola da eliminare", df[mask]["Termine"].tolist(), key="del_select")
            if st.button("Elimina"):
                df = df[df["Termine"] != word_to_delete]
                save_data(df)
                st.success("Parola eliminata con successo.")
                st.rerun()
                
        # Modulo a comparsa per modificare una parola
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

# --- 5. SEZIONE: GENERA FLASHCARD CON AI ---
elif choice == "Genera Flashcard (AI)":
    st.title("Genera Flashcard con AI")
    st.write("Incolla una lista di parole (una per riga). L'AI completerà automaticamente traduzione, categoria ed esempio.")
    
    words_input = st.text_area("Lista parole", height=200)
    
    if st.button("Genera Flashcard", type="primary"):
        if not user_api_key:
            st.error("Inserisci la API Key nella barra laterale.")
        elif not words_input.strip():
            st.warning("Inserisci almeno una parola.")
        else:
            # Pulisce la lista dalle righe vuote
            words_list = [w.strip() for w in words_input.split('\n') if w.strip()]
            
            # Prompt per Gemini 1.5 Flash
            prompt = f"""
            Analizza la seguente lista di parole in tedesco o italiano:
            {words_list}
            
            Per ogni parola, fornisci un output JSON strutturato come una lista di oggetti con le seguenti chiavi esatte:
            - "Termine": La parola originale in tedesco (se l'input era italiano, traduci in tedesco).
            - "Articolo_Plurale": L'articolo determinativo e la forma plurale (solo se è un sostantivo, altrimenti stringa vuota).
            - "Traduzione": La traduzione in italiano.
            - "Categoria": La classificazione grammaticale (es. Verbo, Sostantivo, Aggettivo).
            - "Esempio": Una frase d'esempio naturale in tedesco.
            
            Restituisci SOLO codice JSON valido, senza formattazione markdown aggiuntiva.
            """
            
            with st.spinner("Generazione in corso..."):
                try:
                    # Utilizzo esclusivo del modello richiesto
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt)
                    
                    # Pulizia del testo per estrarre solo il JSON
                    text = response.text.strip()
                    if text.startswith("```json"):
                        text = text[7:-3]
                    elif text.startswith("```"):
                        text = text[3:-3]
                        
                    data = json.loads(text.strip())
                    st.session_state['generated_cards'] = data
                    st.success("Generazione completata! Rivedi i risultati qui sotto.")
                except Exception as e:
                    st.error(f"Errore durante la generazione: {e}")

    # Mostra i risultati generati prima di salvarli
    if 'generated_cards' in st.session_state:
        st.subheader("Revisione Risultati")
        gen_df = pd.DataFrame(st.session_state['generated_cards'])
        edited_gen_df = st.data_editor(gen_df, use_container_width=True)
        
        if st.button("Salva nel Database", type="primary"):
            df = load_data()
            # Imposta i valori di default per le nuove parole
            edited_gen_df["Errori"] = 0
            edited_gen_df["Successi"] = 0
            edited_gen_df["Selezionata"] = False
            
            # Unisce le nuove parole al database esistente
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
        if not user_api_key:
            st.error("Inserisci la API Key nella barra laterale.")
        elif not theme:
            st.warning("Inserisci un tema.")
        else:
            df = load_data()
            vocab = df["Termine"].tolist()
            # Prendiamo un campione di parole per non sovraccaricare l'AI
            vocab_str = ", ".join(vocab[:50]) 
            
            prompt = f"""
            Scrivi un testo in tedesco di livello {level} sul tema: "{theme}".
            Cerca di utilizzare il più possibile le seguenti parole (se pertinenti al tema): {vocab_str}.
            Il testo deve essere naturale e grammaticalmente corretto.
            Restituisci solo il testo in tedesco, senza introduzioni.
            """
            
            with st.spinner("Generazione testo in corso..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt)
                    st.session_state['reader_text'] = response.text
                except Exception as e:
                    st.error(f"Errore: {e}")
                    
    # Mostra il testo e il box per la traduzione contestuale
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
                Fornisci una breve spiegazione del suo utilizzo nel contesto del livello {level}.
                """
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    resp = model.generate_content(prompt_trans)
                    st.success(resp.text)
                except Exception as e:
                    st.error(f"Errore: {e}")

# --- 7. SEZIONE: STUDIO E ALGORITMO ---
elif choice == "Studio":
    st.title("Modalità Studio")
    df = load_data()
    
    if df.empty:
        st.warning("Il database è vuoto. Aggiungi flashcard prima di studiare.")
    else:
        # Impostazioni della sessione
        study_mode = st.radio("Scegli la modalità di ripasso", ["Flashcard", "Test a buchi (Cloze)", "Test Verbi"], horizontal=True)
        session_type = st.radio("Selezione parole", ["Solo flashcard selezionate manualmente", "Smart Random (Scelta automatica)"], horizontal=True)
        
        num_words = 10
        if session_type == "Smart Random (Scelta automatica)":
            num_words = st.number_input("Numero di parole", min_value=1, max_value=100, value=10)
            
        verb_tense = ""
        if study_mode == "Test Verbi":
            verb_tense = st.selectbox("Seleziona il tempo verbale", ["Präsens", "Perfekt", "Präteritum", "Futur I"])
        
        # Avvio della sessione
        if st.button("Inizia Sessione", type="primary"):
            if session_type == "Solo flashcard selezionate manualmente":
                study_df = df[df["Selezionata"] == True]
            else:
                # Algoritmo Spaced Repetition rudimentale: diamo più "peso" alle parole con più errori
                weights = df["Errori"] + 1 
                study_df = df.sample(n=min(num_words, len(df)), weights=weights)
                
            if study_df.empty:
                st.warning("Nessuna parola trovata per i criteri selezionati.")
            else:
                # Salviamo lo stato della sessione
                st.session_state['study_df'] = study_df
                st.session_state['study_index'] = 0
                st.session_state['study_mode'] = study_mode
                st.session_state['verb_tense'] = verb_tense
                st.session_state['session_errors'] = []
                st.rerun()

        # Esecuzione della sessione di studio
        if 'study_df' in st.session_state:
            st.markdown("---")
            study_df = st.session_state['study_df']
            idx = st.session_state['study_index']
            
            # Se ci sono ancora parole da studiare
            if idx < len(study_df):
                row = study_df.iloc[idx]
                st.write(f"Parola {idx + 1} di {len(study_df)}")
                
                # --- A. MODALITA FLASHCARD ---
                if st.session_state['study_mode'] == "Flashcard":
                    st.markdown(f"<h1 class='centered-text'>{row['Termine']}</h1>", unsafe_allow_html=True)
                    if pd.notna(row['Articolo_Plurale']) and row['Articolo_Plurale']:
                        st.markdown(f"<h3 class='centered-text'><i>{row['Articolo_Plurale']}</i></h3>", unsafe_allow_html=True)
                    
                    if st.button("Mostra Traduzione", key=f"show_{idx}"):
                        st.session_state[f"show_trans_{idx}"] = True
                        
                    if st.session_state.get(f"show_trans_{idx}", False):
                        st.markdown(f"<h2 class='centered-text' style='color: #0055ff;'>{row['Traduzione']}</h2>", unsafe_allow_html=True)
                        if pd.notna(row['Esempio']) and row['Esempio']:
                            st.markdown(f"<p class='centered-text'>Esempio: {row['Esempio']}</p>", unsafe_allow_html=True)
                        
                        # Bottoni Swipe Simulato
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Non la so", key=f"fail_{idx}"):
                                df.loc[df["Termine"] == row["Termine"], "Errori"] += 1
                                save_data(df)
                                st.session_state['session_errors'].append(row["Termine"])
                                st.session_state['study_index'] += 1
                                st.rerun()
                        with col2:
                            if st.button("La so", key=f"pass_{idx}"):
                                df.loc[df["Termine"] == row["Termine"], "Successi"] += 1
                                save_data(df)
                                st.session_state['study_index'] += 1
                                st.rerun()
                                
                # --- B. MODALITA CLOZE TEST (Test a buchi) ---
                elif st.session_state['study_mode'] == "Test a buchi (Cloze)":
                    if f"cloze_{idx}" not in st.session_state:
                        prompt = f"Crea una frase in tedesco con uno spazio vuoto (rappresentato da '___') dove dovrebbe essere inserita la parola '{row['Termine']}'. Fornisci anche la traduzione in italiano della frase completa. Restituisci solo la frase e la traduzione."
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            resp = model.generate_content(prompt)
                            st.session_state[f"cloze_{idx}"] = resp.text
                        except Exception as e:
                            st.session_state[f"cloze_{idx}"] = f"Errore di generazione: {e}"
                    
                    st.info(st.session_state[f"cloze_{idx}"])
                    user_answer = st.text_input("Inserisci la parola mancante:", key=f"ans_{idx}")
                    
                    if st.button("Verifica", key=f"check_{idx}", type="primary"):
                        if user_answer.strip().lower() == row['Termine'].lower():
                            st.success("Corretto!")
                            df.loc[df["Termine"] == row["Termine"], "Successi"] += 1
                        else:
                            st.error(f"Sbagliato. La parola corretta era: {row['Termine']}")
                            df.loc[df["Termine"] == row["Termine"], "Errori"] += 1
                            st.session_state['session_errors'].append(row["Termine"])
                        save_data(df)
                        st.session_state[f"checked_{idx}"] = True
                        
                    if st.session_state.get(f"checked_{idx}", False):
                        if st.button("Prossima parola", key=f"next_{idx}"):
                            st.session_state['study_index'] += 1
                            st.rerun()
                            
                # --- C. MODALITA TEST VERBI ---
                elif st.session_state['study_mode'] == "Test Verbi":
                    cat = str(row['Categoria']).lower()
                    if "verb" not in cat:
                        st.info(f"La parola '{row['Termine']}' non è un verbo (Categoria: {row['Categoria']}). Passaggio automatico...")
                        if st.button("Prossima parola", key=f"next_verb_{idx}"):
                            st.session_state['study_index'] += 1
                            st.rerun()
                    else:
                        tense = st.session_state['verb_tense']
                        if f"verb_{idx}" not in st.session_state:
                            prompt = f"Chiedi all'utente di coniugare il verbo tedesco '{row['Termine']}' al tempo {tense}, scegliendo una persona a caso (es. 3a persona singolare). Non fornire la risposta. Scrivi solo la richiesta."
                            try:
                                model = genai.GenerativeModel('gemini-1.5-flash')
                                resp = model.generate_content(prompt)
                                st.session_state[f"verb_{idx}"] = resp.text
                            except Exception as e:
                                st.session_state[f"verb_{idx}"] = f"Errore: {e}"
                                
                        st.info(st.session_state[f"verb_{idx}"])
                        user_answer = st.text_input("Inserisci la coniugazione:", key=f"ans_verb_{idx}")
                        
                        if st.button("Verifica", key=f"check_verb_{idx}", type="primary"):
                            check_prompt = f"L'utente ha risposto '{user_answer}' alla richiesta: '{st.session_state[f'verb_{idx}']} (Verbo originale: {row['Termine']})'. La risposta è corretta? Rispondi solo 'SI' o 'NO'."
                            try:
                                model = genai.GenerativeModel('gemini-1.5-flash')
                                check_resp = model.generate_content(check_prompt)
                                if "SI" in check_resp.text.upper():
                                    st.success("Corretto!")
                                    df.loc[df["Termine"] == row["Termine"], "Successi"] += 1
                                else:
                                    st.error("Sbagliato.")
                                    df.loc[df["Termine"] == row["Termine"], "Errori"] += 1
                                    st.session_state['session_errors'].append(row["Termine"])
                                save_data(df)
                                st.session_state[f"checked_verb_{idx}"] = True
                            except Exception as e:
                                st.error(f"Errore di verifica: {e}")
                                
                        if st.session_state.get(f"checked_verb_{idx}", False):
                            if st.button("Prossima parola", key=f"next_verb_btn_{idx}"):
                                st.session_state['study_index'] += 1
                                st.rerun()

            # Se la sessione è finita
            else:
                st.success("Sessione completata!")
                st.write(f"Parole studiate: {len(study_df)}")
                st.write(f"Errori commessi: {len(st.session_state['session_errors'])}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Ripeti solo le parole sbagliate", type="primary"):
                        if st.session_state['session_errors']:
                            st.session_state['study_df'] = df[df["Termine"].isin(st.session_state['session_errors'])]
                            st.session_state['study_index'] = 0
                            st.session_state['session_errors'] = []
                            st.rerun()
                        else:
                            st.info("Bravissimo! Nessun errore da ripetere.")
                with col2:
                    if st.button("Termina Sessione"):
                        del st.session_state['study_df']
                        del st.session_state['study_index']
                        st.rerun()
