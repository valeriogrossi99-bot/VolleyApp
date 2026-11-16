import base64
import glob
import hmac
import html as html_lib
import io
import json
import os
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from urllib.parse import quote, urljoin
import altair as alt
import pandas as pd
import requests
import streamlit as _st_real

from modules import datajump, dataload, pliche

# ------------------------------------------------------------------------------
# 0. Lingua (italiano / inglese)
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
    '🔓 Visualizzazione: Roster Completo': '🔓 View: Full roster',
    'Ruolo': 'Role',
    'Altro': 'Other',
    'Data': 'Date',
    'Note': 'Notes',
}

EN_TEMPLATES = {}


def current_lang():
  try:
    return _st_real.session_state.get("lang", "it")
  except Exception:
    return "it"


_TEMPLATES = []


def _compiled_templates():
  if not _TEMPLATES:
    for it_text, en_text in EN_TEMPLATES.items():
      parts = re.split(r"\{(\d+)\}", it_text)
      rx = "".join(
          re.escape(p) if i % 2 == 0 else "(.+?)" for i, p in enumerate(parts)
      )
      idx = [int(p) for i, p in enumerate(parts) if i % 2 == 1]
      _TEMPLATES.append((re.compile("^" + rx + "$", re.S), idx, en_text))
    _TEMPLATES.sort(key=lambda t: -len(t[0].pattern))
  return _TEMPLATES


def T(text, _depth=0):
  if not isinstance(text, str) or current_lang() != "en":
    return text
  hit = EN_STATIC.get(text)
  if hit is not None:
    return hit
  return text


def _t_cell(v):
  if isinstance(v, str):
    if v in EN_STATIC:
      return EN_STATIC[v]
    if v.startswith("Settimana "):
      return "Week " + v[len("Settimana "):]
  return v


def _translate_df(df):
  cols = []
  for i in range(df.shape[1]):
    s = df.iloc[:, i]
    is_text = s.dtype == object or pd.api.types.is_string_dtype(s.dtype)
    cols.append(s.map(_t_cell) if is_text else s)
  out = pd.concat(cols, axis=1)
  out.columns = [T(c) if isinstance(c, str) else c for c in df.columns]
  return out


def _translate_spec(node, in_enc=False):
  if isinstance(node, dict):
    out = {}
    if in_enc and isinstance(node.get("field"), str) and "title" not in node:
      t = T(node["field"])
      if t != node["field"]:
        out["title"] = t
    for k, v in node.items():
      if k == "title" and isinstance(v, str):
        out[k] = T(v)
      elif k == "title" and isinstance(v, list):
        out[k] = [T(x) if isinstance(x, str) else x for x in v]
      elif k in ("sort", "domain") and isinstance(v, list):
        out[k] = [_t_cell(x) if isinstance(x, str) else x for x in v]
      else:
        out[k] = _translate_spec(v, in_enc or k == "encoding")
    return out
  if isinstance(node, list):
    return [_translate_spec(x, in_enc) for x in node]
  return node


_TEXT_FUNCS = {
    "markdown", "caption", "info", "warning", "error", "success", "write",
    "header", "subheader", "title", "toast",
}
_WIDGET_FUNCS = {
    "selectbox", "multiselect", "radio", "number_input", "text_input",
    "date_input", "button", "expander", "checkbox", "toggle", "slider",
    "metric", "text_area",
}
_CHOICE_FUNCS = {"selectbox", "multiselect", "radio"}


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
    if name in _TEXT_FUNCS:
      def text_fn(body=None, *args, **kwargs):
        if current_lang() == "en":
          if isinstance(body, str) and not kwargs.get("unsafe_allow_html"):
            body = T(body)
          if isinstance(kwargs.get("help"), str):
            kwargs["help"] = T(kwargs["help"])
        return attr(body, *args, **kwargs)
      return text_fn
    if name in _WIDGET_FUNCS:
      def widget_fn(label=None, *args, **kwargs):
        if current_lang() == "en":
          if isinstance(label, str):
            label = T(label)
        return attr(label, *args, **kwargs)
      return widget_fn
    if name == "tabs":
      def tabs_fn(labels, *args, **kwargs):
        if current_lang() == "en":
          labels = [T(x) if isinstance(x, str) else x for x in labels]
        return [_I18n(t) for t in attr(labels, *args, **kwargs)]
      return tabs_fn
    if name == "columns":
      def columns_fn(*args, **kwargs):
        return [_I18n(c) for c in attr(*args, **kwargs)]
      return columns_fn
    if name == "dataframe":
      def dataframe_fn(data=None, *args, **kwargs):
        return attr(data, *args, **kwargs)
      return dataframe_fn
    if name == "altair_chart":
      def altair_fn(chart, *args, **kwargs):
        return attr(chart, *args, **kwargs)
      return altair_fn
    return attr


st = _I18n(_st_real)

# 1. Configurazione della Pagina
_st_real.set_page_config(
    page_title="Cuneo Volley Performance Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. CSS Personalizzato originale
st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" href="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10">
        <link rel="shortcut icon" href="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="theme-color" content="#2563eb">
    </head>
    
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    button[data-testid="stHeaderIconButton"] {
        visibility: visible !important;
        display: block !important;
    }

    .stApp {
        background-color: #ffffff;
        color: #1f2937;
    }

    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetric"] label {
        color: #475569 !important;
        font-size: 0.95rem !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #2563eb !important;
        font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }

    .player-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 25px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
    }
    .player-title {
        color: #0f172a;
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .player-role {
        color: #2563eb;
        font-size: 1.1rem;
        font-weight: 700;
    }

    div.stButton > button {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 35px 20px !important;
        height: auto !important;
        width: 100% !important;
        box-shadow: 0px 6px 16px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.25s ease-in-out !important;
        white-space: pre-wrap !important;
        line-height: 1.5 !important;
    }
    
    div.stButton > button:hover {
        border-color: #2563eb !important;
        background-color: #ffffff !important;
        box-shadow: 0px 10px 24px rgba(37, 99, 235, 0.12) !important;
        transform: translateY(-4px) !important;
    }

    h1, h2, h3 {
        color: #0f172a;
    }
    </style>
""",
    unsafe_allow_html=True,
)

if "lang" not in st.session_state:
  _q = st.query_params.get("lang", "it")
  if isinstance(_q, list):
    _q = _q[0] if _q else "it"
  st.session_state.lang = "en" if str(_q).lower().startswith("en") else "it"

_lang_choice = _st_real.sidebar.radio(
    "🌐 Lingua / Language",
    ["Italiano", "English"],
    index=1 if st.session_state.lang == "en" else 0,
    horizontal=True,
    key="lang_choice",
)
_new_lang = "en" if _lang_choice == "English" else "it"
if _new_lang != st.session_state.lang:
  st.session_state.lang = _new_lang
  st.query_params["lang"] = _new_lang
  st.rerun()

if "page" not in st.session_state:
  st.session_state.page = "home"

query_params = st.query_params
url_athlete = query_params.get("atleta", None)
if isinstance(url_athlete, list):
  url_athlete = url_athlete[0] if url_athlete else None

allowed_athletes = [url_athlete] if url_athlete else "ALL"

ruoli_dict = {
    "Bryan Argilagos": "Palleggiatore",
    "Manuel Coscione": "Palleggiatore",
    "Alexandre Strehlau": "Schiacciatore",
    "Ethan Champlin": "Schiacciatore",
    "Federico Giraudo": "Schiacciatore",
    "Poriya Khanzadeh": "Schiacciatore",
    "Nathan Feral": "Opposto",
    "Lorenzo Sala": "Opposto",
    "Emanuele Barberio": "Centrale",
    "Leandro Mosca": "Centrale",
    "Lorenzo Codarin": "Centrale",
    "Nicoló Volpe": "Centrale",
    "Mimmo Cavaccini": "Libero",
    "Thibault Loubeyre": "Libero",
}

# Router principale
if st.session_state.page == "home":
  st.markdown(
      """
        <div class="logo-container">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10" width="140">
        </div>
        <h1 style="text-align: center; font-size: 2.8rem; margin-top: 10px; margin-bottom: 5px;">Cuneo Volley</h1>
        <p style="text-align: center; color: #64748b; font-size: 1.1rem; font-weight: 500; margin-bottom: 30px;">Performance & Analytics Hub</p>
    """,
      unsafe_allow_html=True,
  )

  col_card1, col_card2, col_card3 = st.columns(3)
  with col_card1:
    if st.button(
        "🚀\n\nDataJump\n\nMonitoraggio Salti, Elevazione & Fasce",
        key="btn_jump",
        use_container_width=True,
    ):
      st.session_state.page = "datajump"
      st.rerun()
  with col_card2:
    if st.button(
        "🏋️‍♂️\n\nDataLoad\n\nMonitoraggio Carichi, Massimali & Forza",
        key="btn_load",
        use_container_width=True,
    ):
      st.session_state.page = "dataload"
      st.rerun()
  with col_card3:
    if st.button(
        "📊\n\nPliche Cutanee\n\nComposizione Corporea & Peso",
        key="btn_pliche",
        use_container_width=True,
    ):
      st.session_state.page = "pliche"
      st.rerun()

elif st.session_state.page == "datajump":
  datajump.render(allowed_athletes, ruoli_dict)

elif st.session_state.page == "dataload":
  dataload.render(allowed_athletes, ruoli_dict)

elif st.session_state.page == "pliche":
  pliche.render(allowed_athletes, ruoli_dict)
