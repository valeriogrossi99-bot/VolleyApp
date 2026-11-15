import base64
import html as html_lib
import os
import re
import time
import unicodedata
import pandas as pd
import requests
import streamlit as _st_real

# Importiamo i moduli dalle sottosezioni (verranno creati nei prossimi passaggi)
try:
    from modules import datajump, dataload, pliche
except ImportError:
    datajump = dataload = pliche = None

# ------------------------------------------------------------------------------
# 0. Dizionario di Traduzione (Italiano / Inglese)
# ------------------------------------------------------------------------------
EN_STATIC = {
    'Palleggiatore': 'Setter',
    'Schiacciatore': 'Outside Hitter',
    'Opposto': 'Opposite',
    'Centrale': 'Middle Blocker',
    'Libero': 'Libero',
    'Atleta': 'Athlete',
    'Esercizio': 'Exercise',
    '🏠 Torna alla Home': '🏠 Back to Home',
    '🚀\n\nDataJump\n\nMonitoraggio Salti, Elevazione & Fasce': '🚀\n\nDataJump\n\nJump monitoring, elevation & bands',
    '🏋️\u200d♂️\n\nDataLoad\n\nMonitoraggio Carichi, Massimali & Forza': '🏋️\u200d♂️\n\nDataLoad\n\nLoad, max & strength monitoring',
    '📏\n\nPliche Cutanee\n\nAndamento Peso, Pliche & Composizione': '📏\n\nSkinfolds\n\nWeight trend, skinfolds & composition',
}

def current_lang():
    try:
        return _st_real.session_state.get("lang", "it")
    except Exception:
        return "it"

def T(text):
    if not isinstance(text, str) or current_lang() != "en":
        return text
    return EN_STATIC.get(text, text)

# Avvolgitore i18n per Streamlit
class _I18n:
    def __init__(self, target):
        self._target = target
    def __enter__(self):
        return self._target.__enter__()
    def __exit__(self, *args):
        return self._target.__exit__(*args)
    def __getattr__(self, name):
        attr = getattr(self._target, name)
        if name == "sidebar":
            return _I18n(attr)
        if not callable(attr):
            return attr
        if name in {"markdown", "caption", "info", "warning", "error", "success", "write", "header", "subheader", "title", "toast"}:
            def text_fn(body=None, *args, **kwargs):
                if current_lang() == "en" and isinstance(body, str) and not kwargs.get("unsafe_allow_html"):
                    body = T(body)
                return attr(body, *args, **kwargs)
            return text_fn
        return attr

st = _I18n(_st_real)

# 1. Configurazione della Pagina
_st_real.set_page_config(
    page_title="Cuneo Volley Performance Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. CSS Personalizzato
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #ffffff; color: #1f2937; }
    .logo-container { display: flex; justify-content: center; align-items: center; width: 100%; margin-top: 20px; margin-bottom: 10px; }
    div.stButton > button {
        background-color: #f8fafc !important; color: #0f172a !important;
        border: 2px solid #e2e8f0 !important; border-radius: 20px !important;
        padding: 35px 20px !important; height: auto !important; width: 100% !important;
        box-shadow: 0px 6px 16px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.25s ease-in-out !important; white-space: pre-wrap !important; line-height: 1.5 !important;
    }
    div.stButton > button:hover {
        border-color: #2563eb !important; background-color: #ffffff !important;
        box-shadow: 0px 10px 24px rgba(37, 99, 235, 0.12) !important; transform: translateY(-4px) !important;
    }
    h1, h2, h3 { color: #0f172a; }
    </style>
""", unsafe_allow_html=True)

# Selezione Lingua
if "lang" not in st.session_state:
    _q = st.query_params.get("lang", "it")
    st.session_state.lang = "en" if str(_q).lower().startswith("en") else "it"

_lang_choice = _st_real.sidebar.radio("🌐 Lingua / Language", ["Italiano", "English"], index=1 if st.session_state.lang == "en" else 0, horizontal=True)
_new_lang = "en" if _lang_choice == "English" else "it"
if _new_lang != st.session_state.lang:
    st.session_state.lang = _new_lang
    st.query_params["lang"] = _new_lang
    st.rerun()

if "page" not in st.session_state:
    st.session_state.page = "home"

# Gestione Roster e Ruoli base condivisi
ruoli_dict = {
    "Bryan Argilagos": "Palleggiatore", "Manuel Coscione": "Palleggiatore",
    "Alexandre Strehlau": "Schiacciatore", "Ethan Champlin": "Schiacciatore",
    "Federico Giraudo": "Schiacciatore", "Poriya Khanzadeh": "Schiacciatore",
    "Nathan Feral": "Opposto", "Lorenzo Sala": "Opposto",
    "Emanuele Barberio": "Centrale", "Leandro Mosca": "Centrale",
    "Lorenzo Codarin": "Centrale", "Nicoló Volpe": "Centrale",
    "Mimmo Cavaccini": "Libero", "Thibault Loubeyre": "Libero",
}

query_params = st.query_params
url_athlete = query_params.get("atleta", None)
allowed_athletes = [url_athlete[0]] if isinstance(url_athlete, list) and url_athlete else (url_athlete if url_athlete else "ALL")

# ------------------------------------------------------------------------------
# ROUTING DELLE PAGINE
# ------------------------------------------------------------------------------
if st.session_state.page == "home":
    st.markdown("""
        <div class="logo-container">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10" width="140">
        </div>
        <h1 style="text-align: center; font-size: 2.8rem; margin-top: 10px; margin-bottom: 5px;">Cuneo Volley</h1>
        <p style="text-align: center; color: #64748b; font-size: 1.1rem; font-weight: 500; margin-bottom: 30px;">Performance & Analytics Hub</p>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀\n\nDataJump\n\nMonitoraggio Salti, Elevazione & Fasce", use_container_width=True):
            st.session_state.page = "datajump"
            st.rerun()
    with col2:
        if st.button("🏋️‍♂️\n\nDataLoad\n\nMonitoraggio Carichi, Massimali & Forza", use_container_width=True):
            st.session_state.page = "dataload"
            st.rerun()
    with col3:
        if st.button("📏\n\nPliche Cutanee\n\nAndamento Peso, Pliche & Composizione", use_container_width=True):
            st.session_state.page = "pliche"
            st.rerun()

elif st.session_state.page == "datajump":
    if datajump:
        datajump.render(allowed_athletes, ruoli_dict)
    else:
        st.error("Modulo DataJump non trovato nella cartella modules/.")
        if st.button("🏠 Torna alla Home"):
            st.session_state.page = "home"
            st.rerun()

elif st.session_state.page == "dataload":
    if dataload:
        dataload.render(allowed_athletes, ruoli_dict)
    else:
        st.error("Modulo DataLoad non trovato nella cartella modules/.")
        if st.button("🏠 Torna alla Home"):
            st.session_state.page = "home"
            st.rerun()

elif st.session_state.page == "pliche":
    if pliche:
        pliche.render(allowed_athletes, ruoli_dict)
    else:
        st.error("Modulo Pliche non trovato nella cartella modules/.")
        if st.button("🏠 Torna alla Home"):
            st.session_state.page = "home"
            st.rerun()
