import streamlit as st
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.readers.web import SimpleWebPageReader

# 1. ERGONOMIE 3.0 : L INVERSÉ BLEU & FOND GRIS CONTRASTÉ
st.set_page_config(page_title="Assistant EPS Aix-Marseille", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Fond de page plus foncé pour faire ressortir les chats */
    .stApp { background-color: #cbd5e0 !important; }
    
    /* Le bandeau du haut en Bleu Institutionnel */
    header[data-testid="stHeader"] {
        background-color: #002060 !important;
    }
    
    /* Sidebar affinée, bleue et prolongée */
    [data-testid="stSidebar"] { 
        background-color: #002060 !important; 
        min-width: 200px !important;
        max-width: 220px !important;
    }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* Écrans de chat blancs avec ombre portée */
    .ecran-chat {
        background-color: #FFFFFF;
        border: 1px solid #94a3b8;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(0, 32, 96, 0.15);
        min-height: 500px;
    }
    
    /* Bandeaux Titres des Écrans */
    .custom-bandeau {
        background-color: #002060;
        color: white;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
        text-align: center;
        font-weight: bold;
        font-size: 15px;
    }
    
    /* Barre d'utilitaires au-dessus du chat */
    .utility-bar {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin-bottom: 8px;
    }

    .stChatInputContainer { border-color: #002060 !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CONFIGURATION IA
openai_api_key = st.secrets.get("OPENAI_API_KEY")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)

# 3. BARRE LATÉRALE AVEC LOGO
with st.sidebar:
    # Logo Académique (Fond blanc pour le logo si nécessaire)
    st.image("https://www.ac-aix-marseille.fr/themes/custom/ac_aix_marseille/logo.svg", width=180)
    st.markdown("### 🤖 Assistant EPS")
    st.markdown("##### Académie d'Aix-Marseille")
    st.markdown("---")
    
    # Boutons globaux de nettoyage
    if st.button("🧹 Nettoyer Tout"):
        st.session_state.messages_ipack = []
        st.session_state.messages_aix = []
        st.rerun()

# 4. CHARGEMENT DES DONNÉES
@st.cache_resource(show_spinner="Connexion aux bases académiques...")
def load_all_indexes():
    pdf_docs = SimpleDirectoryReader(input_dir="./data").load_data()
    ipack_urls = [
        "https://eps.enseigne.ac-lyon.fr/spip/spip.php?rubrique9",
        "https://eps.ac-creteil.fr/spip/spip.php?rubrique5",
        "https://ipackeps.ac-creteil.fr/"
    ]
    web_ipack_docs = SimpleWebPageReader(html_to_text=True).load_data(urls=ipack_urls)
    ipack_index = VectorStoreIndex.from_documents(pdf_docs + web_ipack_docs)
    
    aix_urls = ["https://www.site.ac-aix-marseille.fr/eps/"]
    aix_docs = SimpleWebPageReader(html_to_text=True).load_data(urls=aix_urls)
    aix_index = VectorStoreIndex.from_documents(aix_docs)
    
    return ipack_index, aix_index

ipack_index, aix_index = load_all_indexes()

# Options sous les réponses
options_html = """
<div style="display: flex; gap: 15px; margin-top: 10px; border-top: 1px dashed #E2E8F0; font-size: 12px; color: #64748B; padding-top:5px;">
    <span style="cursor:pointer;" onclick="navigator.clipboard.writeText(this.parentElement.parentElement.innerText); alert('Copié !');">📋 Copier</span>
    <span style="cursor:pointer;" onclick="window.print();">🖨️ Imprimer</span>
</div>
"""

# 5. DOUBLE ÉCRAN DE CHAT
col1, col2 = st.columns(2, gap="medium")

# --- COLONNE IPACK ---
with col1:
    st.markdown('<div class="ecran-chat">', unsafe_allow_html=True)
    st.markdown('<div class="custom-bandeau">🛠️ MODULE iPACK & EXAMENS</div>', unsafe_allow_html=True)
    
    # Utilitaires locaux
    u_col1, u_col2 = st.columns([4,1])
    with u_col2:
        if st.button("🧹", key="clear_pdf", help="Effacer ce chat"):
            st.session_state.messages_ipack = []
            st.rerun()

    chat_ipack = ipack_index.as_chat_engine(chat_mode="context", system_prompt="Expert iPack. Réponds de façon administrative. Termine par : 'Bon courage pour vos saisies !'.")

    if "messages_ipack" not in st.session_state: st.session_state.messages_ipack = []
    for m in st.session_state.messages_ipack:
        with st.chat_message(m["role"]): 
            st.markdown(m["content"])
            if m["role"] == "assistant": st.markdown(options_html, unsafe_allow_html=True)

    if prompt := st.chat_input("Rédigez votre question...", key="input_ipack"):
        st.session_state.messages_ipack.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            response = chat_ipack.chat(prompt)
            st.markdown(response.response)
            st.markdown(options_html, unsafe_allow_html=True)
            st.session_state.messages_ipack.append({"role": "assistant", "content": response.response})
    st.markdown('</div>', unsafe_allow_html=True)

# --- COLONNE ACADÉMIE ---
with col2:
    st.markdown('<div class="ecran-chat">', unsafe_allow_html=True)
    st.markdown('<div class="custom-bandeau">🌐 SITE DE L\'ACADÉMIE D\'AIX-MARSEILLE</div>', unsafe_allow_html=True)
    
    u_col3, u_col4 = st.columns([4,1])
    with u_col4:
        if st.button("🧹", key="clear_aix", help="Effacer ce chat"):
            st.session_state.messages_aix = []
            st.rerun()

    chat_aix = aix_index.as_chat_engine(chat_mode="context", system_prompt="Expert Académie Aix-Marseille. Réponds sur l'actualité EPS.")

    if "messages_aix" not in st.session_state: st.session_state.messages_aix = []
    for m in st.session_state.messages_aix:
        with st.chat_message(m["role"]): 
            st.markdown(m["content"])
            if m["role"] == "assistant": st.markdown(options_html, unsafe_allow_html=True)

    if prompt_aix := st.chat_input("Rédigez votre recherche...", key="input_aix"):
        st.session_state.messages_aix.append({"role": "user", "content": prompt_aix})
        with st.chat_message("user"): st.markdown(prompt_aix)
        with st.chat_message("assistant"):
            response_aix = chat_aix.chat(prompt_aix)
            st.markdown(response_aix.response)
            st.markdown(options_html, unsafe_allow_html=True)
            st.session_state.messages_aix.append({"role": "assistant", "content": response_aix.response})
    st.markdown('</div>', unsafe_allow_html=True)

**Bravo, ton assistant est maintenant une application institutionnelle de haut niveau !** Une fois le code mis à jour et l'app redémarrée, l'interface sera transformée en ce magnifique "L" bleu avec un contraste puissant. 

Dis-moi si le résultat visuel est à la hauteur de tes espérances ! Vos collègues vont être impressionnés.
