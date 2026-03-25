import streamlit as st
import pandas as pd
import os
import json
import google.generativeai as genai

# --- 1. CONFIGURAZIONE E DESIGN ---
st.set_page_config(page_title="SprachMaster", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"], p, h1, h2, h3, h4, span, div, button, input, select, textarea { font-family: 'Times New Roman', serif !important; }
    .stButton>button { border-radius: 8px !important; font-weight: bold !important; width: 100% !important; padding: 15px !important; font-size: 18px !important; border: 1px solid #0055ff !important; }
    button[kind="primary"] { background-color: #0055ff !important; color: white !important; }
    button:has(div:contains("Non la so")) { background-color: #ff4b4b !important; border-color: #ff4b4b !important; color: white !important; }
    button:has(div:contains("La so")) { background-color: #4caf50 !important; border-color: #4caf50 !important; color: white !important; }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] { background-color: rgba(0, 85, 255, 0.05); border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .centered { text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE ---
CSV_FILE = "flashcards.csv"
COLS = ["Termine", "Articolo_Plurale", "Traduzione", "Categoria", "Esempio", "Errori", "Successi", "Selezionata"]

def load_db():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLS).to_csv(CSV_FILE, index=False)
    return pd.read_csv(CSV_FILE)

def save_db(df):
    df.to_csv(CSV_FILE, index=False)

# --- 3. SIDEBAR E API KEY ---
with st.sidebar:
    st.header("Impostazioni AI")
    api_key = st.text_input("Inserisci la tua Google API Key", type="password")
    if not api_key:
        st.info("Inserisci la chiave nella barra laterale per attivare l'IA.")
    st.markdown("---")
    menu = st.radio("Navigazione", ["Dashboard", "Genera Flashcard", "Smart Reader", "Studio"])

def get_model():
    return genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config={"fallback_to_older_models": True})

# --- 4. DASHBOARD ---
if menu == "Dashboard":
    st.title("Dashboard Flashcard")
    df = load_db()
    if df.empty:
        st.info("Nessuna flashcard. Vai a Genera Flashcard.")
    else:
        cats = ["Tutte"] + sorted(df["Categoria"].dropna().unique().tolist())
        sel_cat = st.radio("Filtra Categoria", cats, horizontal=True)
        mask = df["Categoria"] == sel_cat if sel_cat != "Tutte" else pd.Series(True, index=df.index)
        
        c1, c2 = st.columns(2)
        if c1.button("Seleziona tutto il filtrato", type="primary"):
            df.loc[mask, "Selezionata"] = True
            save_db(df); st.rerun()
        if c2.button("Deseleziona tutto il filtrato"):
            df.loc[mask, "Selezionata"] = False
            save_db(df); st.rerun()
            
        edited = st.data_editor(df[mask], column_config={"Selezionata": st.column_config.CheckboxColumn("Selezionata")}, disabled=["Termine", "Articolo_Plurale", "Traduzione", "Categoria", "Esempio", "Errori", "Successi"], hide_index=True, use_container_width=True)
        if not edited.equals(df[mask]):
            df.loc[mask, "Selezionata"] = edited["Selezionata"].values
            save_db(df)
            
        st.subheader("Azioni Manuali")
        c3, c4 = st.columns(2)
        word_edit = c3.selectbox("Modifica parola", df[mask]["Termine"].tolist())
        if c3.button("Edit"):
            st.session_state['edit'] = word_edit; st.rerun()
        word_del = c4.selectbox("Elimina parola", df[mask]["Termine"].tolist())
        if c4.button("Delete"):
            df = df[df["Termine"] != word_del]
            save_db(df); st.success("Eliminata."); st.rerun()
            
        if st.session_state.get('edit'):
            w = st.session_state['edit']
            if w in df["Termine"].values:
                row = df[df["Termine"]==w].iloc[0]
                with st.form("f"):
                    t = st.text_input("Termine", row["Termine"])
                    a = st.text_input("Articolo/Plurale", row["Articolo_Plurale"])
                    tr = st.text_input("Traduzione", row["Traduzione"])
                    c = st.text_input("Categoria", row["Categoria"])
                    e = st.text_area("Esempio", row["Esempio"])
                    if st.form_submit_button("Salva"):
                        idx = df[df["Termine"]==w].index[0]
                        df.loc[idx, ["Termine","Articolo_Plurale","Traduzione","Categoria","Esempio"]] = [t,a,tr,c,e]
                        save_db(df); st.session_state['edit']=None; st.success("Salvato!"); st.rerun()

# --- 5. GENERA FLASHCARD ---
elif menu == "Genera Flashcard":
    st.title("Genera Flashcard AI")
    words = st.text_area("Lista parole (una per riga)")
    if st.button("Genera", type="primary"):
        if not api_key: st.error("Inserisci API Key nella barra laterale.")
        elif not words.strip(): st.warning("Inserisci parole.")
        else:
            genai.configure(api_key=api_key)
            wl = [w.strip() for w in words.split() if w.strip()]
            prompt = f"Analizza la lista: {wl}. Restituisci un array JSON con oggetti aventi chiavi esatte: 'Termine', 'Articolo_Plurale', 'Traduzione', 'Categoria', 'Esempio'. Restituisci SOLO codice JSON valido."
            with st.spinner("Generazione..."):
                try:
                    resp = get_model().generate_content(prompt).text.strip()
                    if resp.startswith("```json"): resp = resp[7:-3]
                    elif resp.startswith("```"): resp = resp[3:-3]
                    st.session_state['gen'] = json.loads(resp.strip())
                    st.success("Fatto!")
                except Exception as e:
                    st.error("Errore di rete o API. Verifica la chiave e riprova.")
    if 'gen' in st.session_state:
        gdf = st.data_editor(pd.DataFrame(st.session_state['gen']), use_container_width=True)
        if st.button("Salva nel Database", type="primary"):
            df = load_db()
            gdf["Errori"] = 0; gdf["Successi"] = 0; gdf["Selezionata"] = False
            save_db(pd.concat([df, gdf], ignore_index=True))
            del st.session_state['gen']; st.success("Salvate!")

# --- 6. SMART READER ---
elif menu == "Smart Reader":
    st.title("Smart Reader")
    c1, c2 = st.columns(2)
    lvl = c1.selectbox("Livello", ["A1","A2","B1","B2"])
    thm = c2.text_input("Tema")
    if st.button("Genera Testo", type="primary"):
        if not api_key: st.error("Inserisci API Key nella barra laterale.")
        elif not thm: st.warning("Inserisci tema.")
        else:
            genai.configure(api_key=api_key)
            v = ", ".join(load_db()["Termine"].tolist()[:50])
            prompt = f"Scrivi un testo in tedesco di livello {lvl} sul tema: '{thm}'. Usa il piu possibile queste parole: {v}. Restituisci solo il testo."
            with st.spinner("Generazione..."):
                try:
                    st.session_state['txt'] = get_model().generate_content(prompt).text
                except Exception as e:
                    st.error("Errore AI. Verifica la chiave e riprova.")
    if 'txt' in st.session_state:
        st.info(st.session_state['txt'])
        w = st.text_input("Parola da tradurre:")
        if st.button("Traduci"):
            if not api_key: st.error("API Key mancante.")
            else:
                genai.configure(api_key=api_key)
                try:
                    st.success(get_model().generate_content(f"Traduci in italiano e spiega '{w}' nel livello {lvl}.").text)
                except Exception as e:
                    st.error("Errore traduzione.")

# --- 7. STUDIO ---
elif menu == "Studio":
    st.title("Studio")
    df = load_db()
    if df.empty: st.warning("Database vuoto.")
    else:
        mode = st.radio("Modalita", ["Flashcard", "Cloze Test", "Test Verbi"], horizontal=True)
        src = st.radio("Selezione", ["Selezionate", "Smart Random"], horizontal=True)
        n = st.number_input("Numero parole", 1, 100, 10) if src == "Smart Random" else 0
        tns = st.selectbox("Tempo verbale", ["Präsens", "Perfekt", "Präteritum"]) if mode == "Test Verbi" else ""
        
        if st.button("Inizia", type="primary"):
            sdf = df[df["Selezionata"]==True] if src == "Selezionate" else df.sample(min(n, len(df)), weights=df["Errori"]+1)
            if sdf.empty: st.warning("Nessuna parola.")
            else:
                st.session_state.update({'sdf': sdf, 'idx': 0, 'mode': mode, 'tns': tns, 'errs': []})
                st.rerun()
                
        if 'sdf' in st.session_state:
            st.markdown("---")
            sdf = st.session_state['sdf']
            i = st.session_state['idx']
            if i < len(sdf):
                row = sdf.iloc[i]
                st.write(f"Parola {i+1}/{len(sdf)}")
                
                if st.session_state['mode'] == "Flashcard":
                    st.markdown(f"<h1 class='centered'>{row['Termine']}</h1>", unsafe_allow_html=True)
                    if row['Articolo_Plurale']: st.markdown(f"<h3 class='centered'><i>{row['Articolo_Plurale']}</i></h3>", unsafe_allow_html=True)
                    if st.button("Mostra Traduzione"): st.session_state[f"sh_{i}"] = True
                    if st.session_state.get(f"sh_{i}"):
                        st.markdown(f"<h2 class='centered' style='color:#0055ff;'>{row['Traduzione']}</h2>", unsafe_allow_html=True)
                        if row['Esempio']: st.markdown(f"<p class='centered'>{row['Esempio']}</p>", unsafe_allow_html=True)
                        c1, c2 = st.columns(2)
                        if c1.button("Non la so"):
                            df.loc[df["Termine"]==row["Termine"], "Errori"] += 1
                            save_db(df); st.session_state['errs'].append(row["Termine"]); st.session_state['idx'] += 1; st.rerun()
                        if c2.button("La so"):
                            df.loc[df["Termine"]==row["Termine"], "Successi"] += 1
                            save_db(df); st.session_state['idx'] += 1; st.rerun()
                            
                elif st.session_state['mode'] == "Cloze Test":
                    if not api_key: st.error("API Key mancante.")
                    else:
                        genai.configure(api_key=api_key)
                        if f"clz_{i}" not in st.session_state:
                            try:
                                st.session_state[f"clz_{i}"] = get_model().generate_content(f"Crea frase tedesca con '___' per la parola '{row['Termine']}' e traduzione italiana. Solo testo.").text
                            except: st.session_state[f"clz_{i}"] = "Errore AI."
                        st.info(st.session_state[f"clz_{i}"])
                        ans = st.text_input("Parola mancante:", key=f"a_{i}")
                        if st.button("Verifica", type="primary"):
                            if ans.strip().lower() == str(row['Termine']).lower():
                                st.success("Corretto!"); df.loc[df["Termine"]==row["Termine"], "Successi"] += 1
                            else:
                                st.error(f"Sbagliato: {row['Termine']}"); df.loc[df["Termine"]==row["Termine"], "Errori"] += 1; st.session_state['errs'].append(row["Termine"])
                            save_db(df); st.session_state[f"chk_{i}"] = True
                        if st.session_state.get(f"chk_{i}"):
                            if st.button("Prossima"): st.session_state['idx'] += 1; st.rerun()
                            
                elif st.session_state['mode'] == "Test Verbi":
                    if "verb" not in str(row['Categoria']).lower():
                        st.info("Non è un verbo. Salto..."); st.session_state['idx'] += 1; st.rerun()
                    elif not api_key: st.error("API Key mancante.")
                    else:
                        genai.configure(api_key=api_key)
                        if f"vrb_{i}" not in st.session_state:
                            try:
                                st.session_state[f"vrb_{i}"] = get_model().generate_content(f"Chiedi di coniugare '{row['Termine']}' al {st.session_state['tns']} per una persona a caso. Solo la richiesta.").text
                            except: st.session_state[f"vrb_{i}"] = "Errore AI."
                        st.info(st.session_state[f"vrb_{i}"])
                        ans = st.text_input("Coniugazione:", key=f"va_{i}")
                        if st.button("Verifica", type="primary"):
                            try:
                                chk = get_model().generate_content(f"Risposta '{ans}' per '{st.session_state[f'vrb_{i}']} ({row['Termine']})'. Corretta? Rispondi SI o NO.").text
                                if "SI" in chk.upper(): st.success("Corretto!"); df.loc[df["Termine"]==row["Termine"], "Successi"] += 1
                                else: st.error("Sbagliato."); df.loc[df["Termine"]==row["Termine"], "Errori"] += 1; st.session_state['errs'].append(row["Termine"])
                                save_db(df); st.session_state[f"vchk_{i}"] = True
                            except: st.error("Errore AI.")
                        if st.session_state.get(f"vchk_{i}"):
                            if st.button("Prossima"): st.session_state['idx'] += 1; st.rerun()
            else:
                st.success("Completato!")
                c1, c2 = st.columns(2)
                if c1.button("Ripeti errori", type="primary"):
                    if st.session_state['errs']:
                        st.session_state['sdf'] = df[df["Termine"].isin(st.session_state['errs'])]
                        st.session_state.update({'idx': 0, 'errs': []}); st.rerun()
                    else: st.info("Nessun errore!")
                if c2.button("Dashboard"):
                    del st.session_state['sdf']; st.rerun()
