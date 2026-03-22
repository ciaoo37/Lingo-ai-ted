import streamlit as st

st.set_page_config(page_title="Lingo AI", layout="wide")

# Barra laterale
st.sidebar.title("⚙️ Impostazioni")
api_key = st.sidebar.text_input("Inserisci API Key", type="password")

menu = st.sidebar.radio("Menu", ["🏠 Home", "✨ Genera", "📚 Reader", "🧠 Studio"])

# Parte centrale (quella che ora vedi nera)
if menu == "🏠 Home":
    st.title("Benvenuto in Lingo AI! 🇩🇪🇮🇹")
    st.write("Se vedi questa scritta, l'app funziona correttamente!")
    st.info("Inizia cliccando su 'Genera' per creare le tue prime flashcard.")

elif menu == "✨ Genera":
    st.title("✨ Genera Nuove Flashcard")
    parole = st.text_area("Scrivi qui le parole (es: Hund, laufen)")
    if st.button("Genera"):
        st.success(f"Hai scritto: {parole}. (Qui l'AI creerà le card appena metti l'API Key)")

else:
    st.title(f"Sezione {menu}")
    st.write("Questa parte è pronta per essere popolata con i tuoi dati!")
