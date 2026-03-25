import streamlit as st
import pandas as pd
import random

# --- 1. CONFIGURAZIONE PAGINA E DESIGN ---
# Impostiamo il layout largo e il titolo dell'app
st.set_page_config(page_title="SprachMaster: Deutsch-Italienisch", layout="wide", initial_sidebar_state="expanded")

# Inseriamo il CSS personalizzato per rispettare le tue regole di design
# - Font: Times New Roman
# - Colori: Blu primario
# - Bottoni: Grandi e facili da cliccare (Mobile-First)
# - Nessuna emoji
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

# --- 2. GESTIONE DATABASE (SIMULAZIONE LOCALE) ---
# Invece di usare un file CSV che potrebbe dare errori, usiamo la memoria temporanea di Streamlit (session_state)
if 'db' not in st.session_state:
    # Creiamo un database iniziale con alcune parole predefinite per farti provare subito l'app
    dati_iniziali = [
        {"Termine_con_Articolo": "die Katze", "Plurale": "die Katzen", "Traduzione": "il gatto", "Categoria": "Sostantivo", "Esempio": "Die Katze schläft.", "Errori": 0, "Successi": 0, "Selezionata": False},
        {"Termine_con_Articolo": "der Hund", "Plurale": "die Hunde", "Traduzione": "il cane", "Categoria": "Sostantivo", "Esempio": "Der Hund bellt.", "Errori": 0, "Successi": 0, "Selezionata": False},
        {"Termine_con_Articolo": "das Haus", "Plurale": "die Häuser", "Traduzione": "la casa", "Categoria": "Sostantivo", "Esempio": "Das Haus ist groß.", "Errori": 0, "Successi": 0, "Selezionata": False},
        {"Termine_con_Articolo": "lernen", "Plurale": "", "Traduzione": "imparare", "Categoria": "Verbo", "Esempio": "Ich lerne Deutsch.", "Errori": 0, "Successi": 0, "Selezionata": False}
    ]
    st.session_state['db'] = pd.DataFrame(dati_iniziali)

# --- 3. NAVIGAZIONE LATERALE ---
with st.sidebar:
    st.header("Menu di Navigazione")
    menu = ["Dashboard", "Aggiungi Parole", "Smart Reader", "Studio"]
    choice = st.radio("Seleziona Sezione", menu)

# --- 4. SEZIONE: DASHBOARD ---
if choice == "Dashboard":
    st.title("Dashboard Flashcard")
    st.write("Qui puoi visualizzare e gestire il tuo vocabolario.")
    
    df = st.session_state['db']
    
    if df.empty:
        st.info("Nessuna flashcard presente. Vai alla sezione 'Aggiungi Parole' per inserirne di nuove.")
    else:
        # Tabella interattiva per visualizzare e selezionare le parole
        st.subheader("Catalogo Flashcard")
        
        # Mostriamo la tabella permettendo di modificare solo la colonna "Selezionata"
        edited_df = st.data_editor(
            df,
            column_config={
                "Selezionata": st.column_config.CheckboxColumn("Selezionata", help="Seleziona per lo studio manuale"),
            },
            disabled=["Termine_con_Articolo", "Plurale", "Traduzione", "Categoria", "Esempio", "Errori", "Successi"],
            hide_index=True,
            use_container_width=True,
            key="data_editor"
        )
        
        # Salviamo le modifiche fatte alle checkbox nella memoria
        st.session_state['db'] = edited_df

# --- 5. SEZIONE: AGGIUNGI PAROLE (SIMULAZIONE AI) ---
elif choice == "Aggiungi Parole":
    st.title("Genera Flashcard (Simulazione AI)")
    st.write("Incolla una lista di parole (una per riga). Il sistema simulerà l'intelligenza artificiale per completare i dati.")
    
    # Database finto per simulare le risposte dell'AI senza usare internet o API key
    simulazione_ai_db = {
        "katze": {"Termine_con_Articolo": "die Katze", "Plurale": "die Katzen", "Traduzione": "il gatto", "Categoria": "Sostantivo", "Esempio": "Die Katze trinkt Milch."},
        "hund": {"Termine_con_Articolo": "der Hund", "Plurale": "die Hunde", "Traduzione": "il cane", "Categoria": "Sostantivo", "Esempio": "Der Hund spielt im Garten."},
        "flughafen": {"Termine_con_Articolo": "der Flughafen", "Plurale": "die Flughäfen", "Traduzione": "l'aeroporto", "Categoria": "Sostantivo", "Esempio": "Wir fahren zum Flughafen."},
        "apfel": {"Termine_con_Articolo": "der Apfel", "Plurale": "die Äpfel", "Traduzione": "la mela", "Categoria": "Sostantivo", "Esempio": "Ich esse einen Apfel."},
        "gehen": {"Termine_con_Articolo": "gehen", "Plurale": "", "Traduzione": "andare", "Categoria": "Verbo", "Esempio": "Wir gehen nach Hause."}
    }
    
    words_input = st.text_area("Lista parole (es. katze, flughafen, apfel, gehen)", height=150)
    
    if st.button("Genera Flashcard", type="primary"):
        if not words_input.strip():
            st.warning("Inserisci almeno una parola.")
        else:
            # Dividiamo il testo inserito in una lista di parole
            words_list = [w.strip().lower() for w in words_input.split('\n') if w.strip()]
            nuove_righe = []
            
            for word in words_list:
                if word in simulazione_ai_db:
                    # Se la parola è nel nostro finto database AI, la completiamo in automatico
                    dati_parola = simulazione_ai_db[word]
                    dati_parola["Errori"] = 0
                    dati_parola["Successi"] = 0
                    dati_parola["Selezionata"] = False
                    nuove_righe.append(dati_parola)
                    st.success(f"Parola '{word}' elaborata con successo!")
                else:
                    # Se non c'è, la aggiungiamo vuota e avvisiamo l'utente
                    nuova_parola_vuota = {
                        "Termine_con_Articolo": word, "Plurale": "", "Traduzione": "", 
                        "Categoria": "", "Esempio": "", "Errori": 0, "Successi": 0, "Selezionata": False
                    }
                    nuove_righe.append(nuova_parola_vuota)
                    st.warning(f"Parola '{word}' non trovata nel database di simulazione. Verrà aggiunta con campi vuoti da compilare manualmente.")
            
            # Aggiungiamo le nuove parole al database in memoria
            if nuove_righe:
                nuovo_df = pd.DataFrame(nuove_righe)
                st.session_state['db'] = pd.concat([st.session_state['db'], nuovo_df], ignore_index=True)
                st.info("Parole aggiunte al database! Vai alla Dashboard per vederle.")

# --- 6. SEZIONE: SMART READER (SIMULAZIONE) ---
elif choice == "Smart Reader":
    st.title("Smart Reader (Simulazione)")
    st.write("Leggi testi adattati al tuo livello e scopri nuove parole.")
    
    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("Livello di difficoltà", ["A1", "A2", "B1", "B2"])
    with col2:
        theme = st.text_input("Tema della lettura (es. un dialogo in aeroporto)")
        
    if st.button("Genera Testo Simulato", type="primary"):
        if not theme:
            st.warning("Inserisci un tema per generare il testo.")
        else:
            # Testo finto per simulare la generazione
            testo_simulato = f"""
            Guten Tag! Willkommen am Flughafen. 
            Wo ist der Hund? Der Hund ist hier. 
            Die Katze ist nicht am Flughafen. 
            Wir gehen zum Flugzeug. Das Haus ist weit weg.
            """
            st.session_state['reader_text'] = testo_simulato
            st.success("Testo generato con successo!")
            
    if 'reader_text' in st.session_state:
        st.markdown("### Testo Generato")
        st.info(st.session_state['reader_text'])
        
        st.markdown("---")
        st.subheader("Traduzione Contestuale")
        st.write("Inserisci una parola dal testo per vederne la traduzione:")
        
        # Simuliamo il click su una parola usando un campo di testo
        word_to_translate = st.text_input("Parola da tradurre (es. Flughafen, Hund, Katze):")
        
        # Dizionario finto per le traduzioni del testo
        dizionario_testo = {
            "flughafen": "aeroporto",
            "hund": "cane",
            "katze": "gatto",
            "haus": "casa",
            "gehen": "andare",
            "flugzeug": "aeroplano",
            "willkommen": "benvenuto"
        }
        
        if st.button("Traduci"):
            parola_pulita = word_to_translate.strip().lower()
            if parola_pulita in dizionario_testo:
                st.success(f"Traduzione di '{word_to_translate}': **{dizionario_testo[parola_pulita]}**")
            elif parola_pulita:
                st.warning("Traduzione non disponibile nella simulazione per questa parola.")

# --- 7. SEZIONE: STUDIO E ALGORITMO ---
elif choice == "Studio":
    st.title("Modalità Studio")
    df = st.session_state['db']
    
    # Se non c'è una sessione di studio attiva, mostriamo le opzioni per iniziarne una
    if 'study_queue' not in st.session_state:
        st.write("Configura la tua sessione di ripasso.")
        
        session_type = st.radio("Seleziona le parole da studiare:", 
                                ["Solo flashcard selezionate manualmente", "Smart Random (Scelta automatica)"])
        
        num_words = 10
        if session_type == "Smart Random (Scelta automatica)":
            num_words = st.number_input("Quante parole vuoi ripassare?", min_value=1, max_value=100, value=5)
            
        if st.button("Inizia Sessione", type="primary"):
            if session_type == "Solo flashcard selezionate manualmente":
                # Filtriamo solo le righe dove "Selezionata" è True
                parole_da_studiare = df[df["Selezionata"] == True]
            else:
                # Algoritmo Intelligente: diamo più peso (probabilità) alle parole con più errori
                pesi = df["Errori"] + 1 
                numero_reale = min(num_words, len(df))
                parole_da_studiare = df.sample(n=numero_reale, weights=pesi)
                
            if parole_da_studiare.empty:
                st.warning("Nessuna parola trovata. Vai nella Dashboard per selezionare delle parole o aggiungerne di nuove.")
            else:
                # Salviamo le parole da studiare e azzeriamo i contatori della sessione
                st.session_state['study_queue'] = parole_da_studiare.to_dict('records')
                st.session_state['current_index'] = 0
                st.session_state['session_errors'] = []
                st.session_state['show_translation'] = False
                st.rerun()

    # Se c'è una sessione di studio attiva
    else:
        coda_studio = st.session_state['study_queue']
        indice_corrente = st.session_state['current_index']
        
        # Se ci sono ancora carte da mostrare
        if indice_corrente < len(coda_studio):
            carta_corrente = coda_studio[indice_corrente]
            
            st.write(f"Carta {indice_corrente + 1} di {len(coda_studio)}")
            st.markdown("---")
            
            # Mostriamo il termine in tedesco
            st.markdown(f"<h1 class='centered-text'>{carta_corrente['Termine_con_Articolo']}</h1>", unsafe_allow_html=True)
            if carta_corrente['Plurale']:
                st.markdown(f"<h3 class='centered-text'><i>{carta_corrente['Plurale']}</i></h3>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Bottone per mostrare la traduzione
            if not st.session_state['show_translation']:
                if st.button("Mostra Traduzione"):
                    st.session_state['show_translation'] = True
                    st.rerun()
            
            # Se la traduzione è visibile, mostriamo i dettagli e i bottoni di swipe
            if st.session_state['show_translation']:
                st.markdown(f"<h2 class='centered-text' style='color: #0055ff;'>{carta_corrente['Traduzione']}</h2>", unsafe_allow_html=True)
                if carta_corrente['Esempio']:
                    st.markdown(f"<p class='centered-text'>Esempio: {carta_corrente['Esempio']}</p>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Bottoni che simulano lo swipe (Rosso e Verde)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Non la so"):
                        # Registriamo l'errore nel database principale
                        idx_db = df.index[df['Termine_con_Articolo'] == carta_corrente['Termine_con_Articolo']].tolist()[0]
                        st.session_state['db'].at[idx_db, 'Errori'] += 1
                        
                        # Salviamo la carta negli errori della sessione per poterla ripetere alla fine
                        st.session_state['session_errors'].append(carta_corrente)
                        
                        # Passiamo alla carta successiva
                        st.session_state['current_index'] += 1
                        st.session_state['show_translation'] = False
                        st.rerun()
                with col2:
                    if st.button("La so"):
                        # Registriamo il successo nel database principale
                        idx_db = df.index[df['Termine_con_Articolo'] == carta_corrente['Termine_con_Articolo']].tolist()[0]
                        st.session_state['db'].at[idx_db, 'Successi'] += 1
                        
                        # Passiamo alla carta successiva
                        st.session_state['current_index'] += 1
                        st.session_state['show_translation'] = False
                        st.rerun()
                        
        # Se abbiamo finito tutte le carte
        else:
            st.success("Sessione completata!")
            st.write(f"Parole studiate: {len(coda_studio)}")
            st.write(f"Errori commessi: {len(st.session_state['session_errors'])}")
            
            st.markdown("---")
            col_fine1, col_fine2 = st.columns(2)
            
            with col_fine1:
                if st.button("Ripeti solo le parole sbagliate", type="primary"):
                    if len(st.session_state['session_errors']) > 0:
                        # Facciamo ripartire la sessione solo con gli errori
                        st.session_state['study_queue'] = st.session_state['session_errors']
                        st.session_state['current_index'] = 0
                        st.session_state['session_errors'] = []
                        st.session_state['show_translation'] = False
                        st.rerun()
                    else:
                        st.info("Bravissimo! Non hai fatto nessun errore.")
                        
            with col_fine2:
                if st.button("Termina e chiudi sessione"):
                    # Cancelliamo i dati della sessione per tornare alla schermata iniziale dello Studio
                    del st.session_state['study_queue']
                    del st.session_state['current_index']
                    del st.session_state['session_errors']
                    del st.session_state['show_translation']
                    st.rerun()
