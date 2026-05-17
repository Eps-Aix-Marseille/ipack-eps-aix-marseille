import streamlit as st
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI

# 1. ERGONOMIE & CHARTE GRAPHIQUE
st.set_page_config(page_title="Assistant EPS Aix-Marseille", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }
    .stApp { background-color: #cbd5e0 !important; }
    header[data-testid="stHeader"] { background-color: #002060 !important; }
    [data-testid="stSidebar"] { background-color: #002060 !important; min-width: 190px !important; max-width: 210px !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    .custom-bandeau { background-color: #002060; color: white; padding: 12px; border-radius: 8px; margin-bottom: 10px; text-align: center; font-weight: bold; font-size: 15px; }
    [data-testid="stVerticalBlock"] > div:has(div.stChatMessage) { background-color: #FFFFFF !important; border: 1px solid #94a3b8 !important; border-radius: 12px !important; padding: 15px !important; }
    .stChatInputContainer { border-color: #002060 !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CONFIGURATION IA
openai_api_key = st.secrets.get("OPENAI_API_KEY")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)

# 3. BARRE LATÉRALE
with st.sidebar:
    if os.path.exists("images_7.png"): # Corrigé selon le nom exact sur ton GitHub
        st.image("images_7.png", width=170)
    elif os.path.exists("image_7.png"):
        st.image("image_7.png", width=170)
    st.markdown("### 🤖 Assistant EPS")
    st.markdown("##### Académie d'Aix-Marseille")
    st.markdown("---")

# 4. CHARGEMENT UNIQUEMENT DES DOCUMENTS LOCAUX (Fini le blocage des sites web !)
@st.cache_resource(show_spinner="Connexion sécurisée aux bases académiques...")
def load_all_indexes():
    # On force la création d'un index même si le dossier data est vide au début
    if not os.path.exists("./data") or len(os.listdir("./data")) == 0:
        os.makedirs("./data", exist_ok=True)
        with open("./data/info.txt", "w") as f:
            f.write("Base de données initialisée.")
            
    pdf_docs = SimpleDirectoryReader(input_dir="./data").load_data()
    index = VectorStoreIndex.from_documents(pdf_docs)
    return index, index

ipack_index, aix_index = load_all_indexes()

options_html = """<div style="display: flex; gap: 15px; margin-top: 10px; border-top: 1px dashed #E2E8F0; font-size: 11px; color: #64748B; padding-top:5px;"><span style="cursor:pointer;" onclick="navigator.clipboard.writeText(this.parentElement.parentElement.innerText); alert('Texte copié !');">📋 Copier</span></div>"""

# 5. DOUBLE ÉCRAN
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="custom-bandeau">🛠️ RECHERCHE iPACK & EXAMENS</div>', unsafe_allow_html=True)
    if os.path.exists("image_5.png"): st.image("image_5.png", width=130)
    
    zone_ipack = st.container()
    with zone_ipack:
        chat_ipack = ipack_index.as_chat_engine(chat_mode="context", system_prompt="Tu es l'Assistant iPack. Réponds de façon concise. Termine par 'Bon courage pour vos saisies !'.")
        if "messages_ipack" not in st.session_state: st.session_state.messages_ipack = []
        with st.chat_message("assistant"): st.markdown("💬 **Système iPack prêt.** Posez votre question.")
        for m in st.session_state.messages_ipack:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    prompt = st.chat_input("Rédigez votre question...", key="input_ipack")

with col2:
    st.markdown('<div class="custom-bandeau">🌐 SITE DE L\'ACADÉMIE D\'AIX-MARSEILLE</div>', unsafe_allow_html=True)
    if os.path.exists("image_6.png"): st.image("image_6.png", width=75)
    
    zone_aix = st.container()
    with zone_aix:
        chat_aix = aix_index.as_chat_engine(chat_mode="context", system_prompt="Tu es l'Assistant du site EPS.")
        if "messages_aix" not in st.session_state: st.session_state.messages_aix = []
        with st.chat_message("assistant"): st.markdown("💬 **Portail Académique prêt.**")
        for m in st.session_state.messages_aix:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    prompt_aix = st.chat_input("Rédigez votre recherche...", key="input_aix")

# 6. EXECUTION
if prompt:
    st.session_state.messages_ipack.append({"role": "user", "content": prompt})
    with zone_ipack:
        with st.chat_message("assistant"):
            response = chat_ipack.chat(prompt)
            st.markdown(response.response)
    st.rerun()

if prompt_aix:
    st.session_state.messages_aix.append({"role": "user", "content": prompt_aix})
    with zone_aix:
        with st.chat_message("assistant"):
            response_aix = chat_aix.chat(prompt_aix)
            st.markdown(response_aix.response)
    st.rerun()
