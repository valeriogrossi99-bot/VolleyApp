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
import streamlit as st

# 1. Configurazione della Pagina
st.set_page_config(
    page_title="Cuneo Volley Performance Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. CSS Personalizzato
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


    /* UI refresh: cleaner spacing, softer surfaces and clearer interaction states */
    :root { --cv-blue: #155eef; --cv-navy: #102a43; --cv-line: #dbe5f0; }
    .block-container { padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1600px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #f7faff 0%, #edf3fa 100%); }
    [data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }
    [data-testid="stMetric"] { border-radius: 16px !important; border: 1px solid var(--cv-line) !important; box-shadow: 0 5px 18px rgba(16,42,67,.055) !important; }
    [data-testid="stTabs"] button[role="tab"] { border-radius: 10px 10px 0 0; padding: .65rem 1rem; font-weight: 650; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] { gap: 1rem; }
    div.stButton > button { border-radius: 14px !important; border-width: 1px !important; min-height: 4rem; }
    div.stButton > button:focus-visible { outline: 3px solid rgba(21,94,239,.35) !important; outline-offset: 2px; }
    [data-testid="stDataFrame"] { border: 1px solid var(--cv-line); border-radius: 12px; overflow: hidden; }
    [data-testid="stExpander"] { border: 1px solid var(--cv-line); border-radius: 12px; }
    .language-label { color: #334155; font-size: .9rem; padding: .25rem 0 .35rem; }
    @media (max-width: 768px) {
      .block-container { padding-left: 1rem; padding-right: 1rem; }
      .player-card { padding: 16px; }
      div.stButton > button { padding: 22px 14px !important; }
    }
    </style>
""",
    unsafe_allow_html=True,
)


# 2B. Lingua dell'interfaccia (la scelta resta valida durante la sessione)
if "app_language" not in st.session_state:
    st.session_state.app_language = "Italiano"
st.sidebar.markdown("<div class='language-label'>🌐 <b>Language / Lingua</b></div>", unsafe_allow_html=True)
st.sidebar.selectbox(
    "Lingua / Language",
    ["Italiano", "English"],
    key="app_language",
    label_visibility="collapsed",
)

# Traduzioni UI: i valori e i nomi originali dei dati degli atleti non vengono modificati.
_EN_PHRASES = {
    "Cuneo Volley Performance Hub": "Cuneo Volley Performance Hub",
    "Performance & Analytics Hub": "Performance & Analytics Hub",
    "Monitoraggio Salti, Elevazione & Fasce": "Jump, Height & Zone Monitoring",
    "Monitoraggio Carichi, Massimali & Forza": "Load, Max Strength & Performance Monitoring",
    "Monitoraggio Salti & Elevazione": "Jump & Elevation Monitoring",
    "Carichi, Massimali & Valutazione Forza": "Loads, Max Strength & Strength Assessment",
    "Torna alla Home": "Back to Home",
    "Roster Completo": "Full Roster",
    "Visualizzazione Dedicata": "Dedicated View",
    "Filtri Selezione & Confronto": "Selection & Comparison Filters",
    "Filtra per Ruolo": "Filter by Position",
    "Nessun file CSV relativo ai salti trovato.": "No jump-tracking CSV files found.",
    "Schede Settimanali": "Weekly Training Plans",
    "Carichi & Massimali (tutti gli esercizi)": "Loads & Max Strength (all exercises)",
    "Valutazione Forza & 1RM (Google Sheet)": "Strength Assessment & 1RM (Google Sheet)",
    "Tonnellaggio & Volume Pesi": "Tonnage & Weight-Training Volume",
    "Inserisci Carichi": "Enter Loads",
    "Schede Settimanali (lette dai tuoi Google Fogli)": "Weekly Training Plans (from Google Sheets)",
    "File e schede lette": "Files and plans read",
    "Ricarica le schede ora": "Reload training plans",
    "Nessun carico per questa settimana e questa seduta.": "No loads found for this week and session.",
    "Inserisci una serie": "Enter a Set",
    "Verifica collegamento con il Google Sheet": "Check Google Sheets connection",
    "Esegui verifica": "Run check",
    "Scrittura": "Write",
    "Lettura": "Read",
    "Giocatore": "Player",
    "Giocatori": "Players",
    "Atleta": "Athlete",
    "Ruolo": "Position",
    "Data": "Date",
    "Note (facoltativo)": "Notes (optional)",
    "Salva serie": "Save set",
    "Nome del nuovo esercizio": "New exercise name",
    "Nessun carico registrato per ora.": "No loads recorded yet.",
    "Carichi, Massimali & Andamento per Esercizio": "Loads, Max Strength & Exercise Trends",
    "Tonnellaggio Sollevato per Data e Giocatore (kg)": "Tonnage by Date and Player (kg)",
    "Data Seduta Pesi": "Strength Session Date",
    "Tonnellaggio Totale (kg)": "Total Tonnage (kg)",
    "Nessun dato di tonnellaggio disponibile.": "No tonnage data available.",
    "Salto Max (cm)": "Max Jump (cm)",
    "Volume Salti Settimanali": "Weekly Jump Volume",
    "Totale Salti per Giocatore": "Total Jumps by Player",
    "Salto Max (cm) per Giocatore": "Max Jump (cm) by Player",
    "Confronto tra due settimane di lavoro": "Compare Two Training Weeks",
    "Servono dati di almeno due settimane per fare il confronto.": "At least two weeks of data are needed for comparison.",
    "Scegli due settimane diverse per il confronto.": "Choose two different weeks to compare.",
    "Volume Salti per Giorno": "Jump Volume by Day",
    "Salto Max (cm) per Giorno": "Max Jump (cm) by Day",
    "Distribuzione Fasce (% sui salti della settimana)": "Jump Zone Distribution (% of weekly jumps)",
    "Dettaglio per Giorno": "Daily Details",
    "Confronto per Giocatore": "Player Comparison",
    "Scheda di": "Training Plan for",
    "Massimali di": "Max Strength for",
    "Andamento di": "Progress for",
    "Filtra per": "Filter by",
    "Tutti": "All",
    "Settimana": "Week",
    "Sessione": "Session",
    "Esercizio": "Exercise",
    "Carico": "Load",
    "Ripetizioni": "Repetitions",
    "Serie": "Sets",
    "kg sollevati": "weight lifted (kg)",
    "Scrivi il nome dell'esercizio.": "Enter the exercise name.",
    "Inserisci i kg sollevati.": "Enter the lifted weight in kg.",
    "Impossibile caricare il foglio Google di valutazione della forza.": "Unable to load the Google Sheet for strength assessment.",
    "Modalità modifica attiva": "Edit mode enabled",
    "Modalità modifica non attiva": "Edit mode is not enabled",
    "Nessuna sessione trovata con i filtri attuali.": "No sessions match the current filters.",
    "Pallino arancione = giorno di partita": "Orange dot = match day",
    "Colonna / pallino arancione = giorno di partita": "Orange bar/dot = match day",
    "Lingua / Language": "Language",
    "Palleggiatore": "Setter",
    "Schiacciatore": "Outside Hitter",
    "Opposto": "Opposite",
    "Centrale": "Middle Blocker",
    "Libero": "Libero",
    "Altezza": "Height",
    "Classe": "Born",
    "Nessuna cartella o file collegato.": "No linked folder or file found.",
    "File CSV trovati": "CSV files found",
    "sedute caricate": "sessions loaded",
    "Ultime serie registrate per questo esercizio": "Latest sets recorded for this exercise",
    "Calcolo con questa serie": "Calculation for this set",
    "Valore": "Value",
    "Risultato": "Result",
    "Confronto": "Comparison",
    "Seleziona": "Select",
    "Selezione atleta": "Player selection",
    "Filtri": "Filters",
    "Visualizzazione": "View",
    "Nessun dato disponibile.": "No data available.",
    "Nessun dato trovato.": "No data found.",
    "Nessun risultato": "No results",
    "Ultime 7 sedute": "Last 7 sessions",
    "per Giocatore": "by Player",
    "per Giorno": "by Day",
    "per Esercizio": "by Exercise",
    "Volume": "Volume",
    "Carico Totale": "Total Load",
    "Massimale": "One-Rep Max",
    "Massimali": "Max Strength",
    "Valutazione Forza": "Strength Assessment",
    "Settimane": "Weeks",
    "Settimana di lavoro": "Training Week",
    "Giorno": "Day",
    "Sessione pesi": "Strength Session",
    "Seduta": "Session",
    "Fascia": "Zone",
    "Percentuale": "Percentage",
    "Totale": "Total",
    "Media": "Average",
    "Minimo": "Minimum",
    "Massimo": "Maximum",
    "Andamento": "Trend",
}

def _translate_ui(value):
    if st.session_state.get("app_language", "Italiano") != "English":
        return value
    if isinstance(value, str):
        # Lascia invariati blocchi CSS/HTML strutturali e traduce i testi visibili.
        if "<style" in value or "<head>" in value:
            return value
        out = value
        for src in sorted(_EN_PHRASES, key=len, reverse=True):
            out = out.replace(src, _EN_PHRASES[src])
        return out
    return value

def _wrap_ui_method(obj, name, positions=(0,)):
    original = getattr(obj, name, None)
    if not callable(original):
        return
    def wrapped(*args, **kwargs):
        args = list(args)
        for pos in positions:
            if pos < len(args):
                if name == "tabs" and isinstance(args[pos], (list, tuple)):
                    args[pos] = [_translate_ui(item) for item in args[pos]]
                else:
                    args[pos] = _translate_ui(args[pos])
        for key in ("label", "help", "placeholder"):
            if key in kwargs and isinstance(kwargs[key], str):
                kwargs[key] = _translate_ui(kwargs[key])
        return original(*args, **kwargs)
    try:
        setattr(obj, name, wrapped)
    except Exception:
        pass

# Intercetta solo testi dell'interfaccia; opzioni e dati degli atleti restano intatti.
for _method in ("markdown", "title", "header", "subheader", "caption", "write", "text",
                "info", "warning", "error", "success", "exception", "button", "metric",
                "selectbox", "multiselect", "text_input", "text_area", "number_input",
                "date_input", "time_input", "checkbox", "radio", "file_uploader", "download_button"):
    _wrap_ui_method(st, _method)
    _wrap_ui_method(st.sidebar, _method)
_wrap_ui_method(st, "tabs")
_wrap_ui_method(st.sidebar, "tabs")

# 3. Inizializzazione Sessione e Gestione Parametri URL
if "page" not in st.session_state:
  st.session_state.page = "home"

# Lettura robusta del parametro dall'URL
query_params = st.query_params
url_athlete = query_params.get("atleta", None)

if isinstance(url_athlete, list):
  url_athlete = url_athlete[0] if url_athlete else None

if url_athlete:
  allowed_athletes = [url_athlete]
else:
  allowed_athletes = "ALL"

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

cognomi_to_full = {
    "Argilagos": "Bryan Argilagos",
    "Coscione": "Manuel Coscione",
    "Strehlau": "Alexandre Strehlau",
    "Champlin": "Ethan Champlin",
    "Giraudo": "Federico Giraudo",
    "Poriya": "Poriya Khanzadeh",
    "Feral": "Nathan Feral",
    "Sala": "Lorenzo Sala",
    "Barberio": "Emanuele Barberio",
    "Mosca": "Leandro Mosca",
    "Codarin": "Lorenzo Codarin",
    "Volpe": "Nicoló Volpe",
    "Cavaccini": "Mimmo Cavaccini",
    "Loubeyre": "Thibault Loubeyre",
}

player_info = {
    "Bryan Argilagos": {
        "bio": "Palleggiatore | Altezza: 200 cm | Classe 2007",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Manuel Coscione": {
        "bio": "Palleggiatore | Altezza: 188 cm | Classe 1980",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Alexandre Strehlau": {
        "bio": "Schiacciatore | Altezza: 199 cm | Classe 2004",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Ethan Champlin": {
        "bio": "Schiacciatore | Altezza: 191 cm | Classe 2001",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Federico Giraudo": {
        "bio": "Schiacciatore | Altezza: 198 cm | Classe 2007",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Poriya Khanzadeh": {
        "bio": "Schiacciatore | Altezza: 202 cm | Classe 2004",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Nathan Feral": {
        "bio": "Opposto | Altezza: 197 cm | Classe 2003",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Lorenzo Sala": {
        "bio": "Opposto | Altezza: 200 cm | Classe 2002",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Emanuele Barberio": {
        "bio": "Centrale | Altezza: 202 cm | Classe 2007",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Leandro Mosca": {
        "bio": "Centrale | Altezza: 209 cm | Classe 2000",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Lorenzo Codarin": {
        "bio": "Centrale | Altezza: 199 cm | Classe 1996",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Nicoló Volpe": {
        "bio": "Centrale | Altezza: 193 cm | Classe 2003",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
}

MATCH_DAYS = {
    "2026-10-18",
    "2026-10-25",
    "2026-11-01",
    "2026-11-04",
    "2026-11-08",
    "2026-11-22",
    "2026-11-29",
    "2026-12-02",
    "2026-12-06",
    "2026-12-13",
    "2026-12-20",
    "2026-12-26",
    "2027-01-03",
    "2027-01-10",
    "2027-01-13",
    "2027-01-17",
    "2027-01-24",
    "2027-01-31",
    "2027-02-14",
    "2027-02-21",
    "2027-02-24",
    "2027-02-28",
}

ANCHOR_MONDAY = pd.to_datetime("2026-10-05")

# Nomi possibili della colonna con l'orario, se nei CSV è separata dalla data
TIME_COLUMNS = {"TIME", "ORA", "ORARIO", "HOUR"}

GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
BAND_ORDER = [
    "JUMPS < 30",
    "JUMPS 30-50",
    "JUMPS 50-60",
    "JUMPS 60-70",
    "JUMPS > 70",
]


# ------------------------------------------------------------------------------
# Foto e scheda Lega Pallavolo Serie A dei giocatori
# ------------------------------------------------------------------------------
LEGA_BASE = "https://www.legavolley.it"
# ID della squadra sul sito Lega (Acqua Sant'Anna Cuneo, SuperLega 2026/27).
# Cambia a ogni stagione: se le foto Lega non compaiono più, aggiornalo.
LEGA_TEAM_ID = 6863
CUNEO_ROSTER_URL = "https://cuneovolley.it/prima-squadra/giocatori"
# Ordine delle fonti per la foto: prima il sito Cuneo Volley, poi la Lega.
# Per invertire: ["lega", "cuneo"]
PHOTO_SOURCE_ORDER = ["cuneo", "lega"]
REQ_HEADERS = {"User-Agent": "Mozilla/5.0 (Cuneo Volley Performance Hub)"}

# Codici giocatore del sito Lega (formato: 3 lettere cognome - 3 lettere nome
# - anno di nascita). Servono solo come ripiego: se la pagina squadra della Lega
# è leggibile, i codici reali vengono presi da lì in automatico.
LEGA_PLAYER_IDS = {
    "Bryan Argilagos": "ARG-BRY-07",
    "Manuel Coscione": "COS-MAN-80",
    "Alexandre Strehlau": "STR-ALE-04",
    "Ethan Champlin": "CHA-ETH-01",
    "Federico Giraudo": "GIR-FED-07",
    "Poriya Khanzadeh": "KHA-POR-04",
    "Nathan Feral": "FER-NAT-03",
    "Lorenzo Sala": "SAL-LOR-02",
    "Emanuele Barberio": "BAR-EMA-07",
    "Leandro Mosca": "MOS-LEA-00",
    "Lorenzo Codarin": "COD-LOR-96",
    "Nicoló Volpe": "VOL-NIC-03",
    "Mimmo Cavaccini": "CAV-DOM-87",
    "Thibault Loubeyre": "LOU-THI-01",
}


def _ascii_lower(text):
  text = unicodedata.normalize("NFKD", str(text))
  return text.encode("ascii", "ignore").decode().lower()


def _slug(text):
  return re.sub(r"[^a-z]", "", _ascii_lower(text))


def _tokens(text):
  return {t for t in re.split(r"[^a-z]+", _ascii_lower(text)) if t}


# cognome normalizzato -> nome completo usato nell'app
SURNAME_TO_PLAYER = {_slug(n.split()[-1]): n for n in ruoli_dict}


def _html_attr(tag, names):
  for n in names:
    m = re.search(
        rf"(?<![\w-]){n}\s*=\s*[\"']([^\"']*)[\"']", tag, flags=re.I
    )
    if m and m.group(1).strip():
      return html_lib.unescape(m.group(1).strip())
  return None


def _fetch_html(url, timeout=10):
  try:
    r = requests.get(url, headers=REQ_HEADERS, timeout=timeout)
    if r.status_code == 200:
      return r.text
  except Exception:
    pass
  return ""


def _download_image(url, max_bytes=6_000_000):
  try:
    r = requests.get(url, headers=REQ_HEADERS, timeout=12)
    ctype = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
    if (
        r.status_code != 200
        or not ctype.startswith("image/")
        or not r.content
        or len(r.content) > max_bytes
    ):
      return None
    return r.content, ctype
  except Exception:
    return None


def _to_data_uri(raw, ctype):
  """Ridimensiona la foto (se possibile) e la incorpora come data URI."""
  try:
    from PIL import Image

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.thumbnail((500, 500))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    raw, ctype = buf.getvalue(), "image/jpeg"
  except Exception:
    pass
  return f"data:{ctype};base64," + base64.b64encode(raw).decode()


@st.cache_data(ttl=600, show_spinner=False)
def load_cuneo_site_photos():
  """Foto dalla pagina 'I giocatori' del sito Cuneo Volley: {nome: url}."""
  html = _fetch_html(CUNEO_ROSTER_URL)
  photos = {}
  for tag in re.findall(r"<img\b[^>]*>", html, flags=re.I):
    src = _html_attr(tag, ["data-src", "data-lazy-src", "data-original", "src"])
    if not src or "/storage/images/" not in src:
      continue
    text = " ".join(
        filter(
            None,
            [
                _html_attr(tag, ["alt"]),
                _html_attr(tag, ["title"]),
                src.rsplit("/", 1)[-1],
            ],
        )
    )
    toks = _tokens(text)
    for surname, full in SURNAME_TO_PLAYER.items():
      if surname in toks and full not in photos:
        photos[full] = urljoin(CUNEO_ROSTER_URL, src)
        break
  return photos


@st.cache_data(ttl=3600, show_spinner=False)
def load_lega_player_ids():
  """Codici giocatore Lega: parte dal ripiego e usa quelli reali del sito."""
  ids = dict(LEGA_PLAYER_IDS)
  html = _fetch_html(f"{LEGA_BASE}/team/{LEGA_TEAM_ID}")
  for m in re.finditer(
      r"<a\b[^>]*href=[\"'][^\"']*?/player/([A-Za-z0-9\-]+)[^\"']*[\"'][^>]*>(.*?)</a>",
      html,
      flags=re.I | re.S,
  ):
    key = m.group(1).upper()
    toks = _tokens(re.sub(r"<[^>]+>", " ", m.group(2)))
    for surname, full in SURNAME_TO_PLAYER.items():
      if surname in toks:
        ids[full] = key
        break
  return ids


@st.cache_data(ttl=600, show_spinner=False)
def get_player_photo(full_name):
  """Foto del giocatore come data URI (None se nessuna fonte è disponibile)."""
  lega_ids = load_lega_player_ids()
  candidates = {
      "cuneo": load_cuneo_site_photos().get(full_name),
      "lega": (
          f"{LEGA_BASE}/Foto.aspx?Key={lega_ids[full_name]}"
          f"&sqid={LEGA_TEAM_ID}&heightImg=400"
          if full_name in lega_ids
          else None
      ),
  }
  for source in PHOTO_SOURCE_ORDER:
    url = candidates.get(source)
    if not url:
      continue
    got = _download_image(url)
    if got:
      return _to_data_uri(*got)
  return None


def get_custom_week(dt_series):
  days_diff = (dt_series.dt.normalize() - ANCHOR_MONDAY).dt.days
  week_offset = days_diff // 7
  return "Settimana " + (7 + week_offset).astype(int).astype(str)


def extract_week_num(w_str):
  try:
    return int(w_str.replace("Settimana ", ""))
  except Exception:
    return 0


def get_csv_files():
  files = (
      glob.glob("data/*.csv")
      + glob.glob("data/*.CSV")
      + glob.glob("*.csv")
      + glob.glob("*.CSV")
  )
  return sorted(set(files))


def get_files_signature():
  """Elenco dei CSV con data di modifica e dimensione.

  Viene passato alle funzioni di caricamento: se aggiungi o modifichi un file
  la firma cambia e la cache viene ricalcolata in automatico.
  """
  sig = []
  for f in get_csv_files():
    try:
      sig.append((f, os.path.getmtime(f), os.path.getsize(f)))
    except OSError:
      pass
  return tuple(sig)


@st.cache_data(ttl=60)
def load_jump_data(files_signature):
  files = [s[0] for s in files_signature]
  df_list = []
  for f in files:
    try:
      temp = pd.read_csv(f, sep=";")
      temp.columns = temp.columns.str.strip()
      if "JUMP HEIGHT(cm)" in temp.columns:
        df_list.append(temp)
    except Exception:
      pass
  if not df_list:
    return pd.DataFrame()
  df = pd.concat(df_list, ignore_index=True)
  df.columns = df.columns.str.strip()

  # Altezza salto numerica (accetta anche la virgola come decimale)
  df["JUMP HEIGHT(cm)"] = pd.to_numeric(
      df["JUMP HEIGHT(cm)"].astype(str).str.replace(",", ".", regex=False),
      errors="coerce",
  )
  df = df.dropna(subset=["JUMP HEIGHT(cm)"]).copy()

  df["ATHLETE"] = (
      df["NAME"].astype(str).str.strip()
      + " "
      + df["SURNAME"].astype(str).str.strip()
  )
  df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")

  # Data e orario
  df["DATE_DT"] = pd.to_datetime(df["DATE"], errors="coerce")
  df = df.dropna(subset=["DATE_DT"]).copy()

  time_col = next((c for c in df.columns if c.upper() in TIME_COLUMNS), None)
  date_has_time = (
      (df["DATE_DT"].dt.hour != 0)
      | (df["DATE_DT"].dt.minute != 0)
      | (df["DATE_DT"].dt.second != 0)
  ).any()

  df["DATETIME"] = df["DATE_DT"]
  df["HAS_TIME"] = bool(date_has_time)

  if not date_has_time and time_col is not None:
    combined = pd.to_datetime(
        df["DATE_DT"].dt.strftime("%Y-%m-%d")
        + " "
        + df[time_col].astype(str).str.strip(),
        errors="coerce",
    )
    if combined.notna().any():
      df["DATETIME"] = combined.fillna(df["DATE_DT"])
      df["HAS_TIME"] = True

  df["DATE_DT"] = df["DATE_DT"].dt.normalize()
  df["DATE_STR"] = df["DATE_DT"].dt.strftime("%Y-%m-%d")
  df["WEEK"] = get_custom_week(df["DATE_DT"])
  df["IS_MATCH"] = df["DATE_STR"].isin(MATCH_DAYS)

  def classify_jump(h):
    try:
      val = float(h)
    except Exception:
      return "Altro"
    if val < 30:
      return "JUMPS < 30"
    elif 30 <= val <= 50:
      return "JUMPS 30-50"
    elif 50 < val <= 60:
      return "JUMPS 50-60"
    elif 60 < val <= 70:
      return "JUMPS 60-70"
    else:
      return "JUMPS > 70"

  df["JUMP_BAND"] = df["JUMP HEIGHT(cm)"].apply(classify_jump)
  return df


@st.cache_data(ttl=60)
def load_load_data(files_signature):
  files = [s[0] for s in files_signature]
  df_list = []
  for f in files:
    try:
      temp = pd.read_csv(f, sep=";")
      if any(c in temp.columns for c in ["TONNAGE", "WEIGHT(kg)", "LOAD(kg)", "RPE"]):
        df_list.append(temp)
    except Exception:
      pass
  if not df_list:
    return pd.DataFrame()
  df = pd.concat(df_list, ignore_index=True)
  df.columns = df.columns.str.strip()
  if "NAME" in df.columns and "SURNAME" in df.columns:
    df["ATHLETE"] = (
        df["NAME"].astype(str).str.strip()
        + " "
        + df["SURNAME"].astype(str).str.strip()
    )
  else:
    df["ATHLETE"] = "Atleta Generico"
  df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")
  date_col = "DATE" if "DATE" in df.columns else "Data"
  df["DATE_DT"] = pd.to_datetime(df[date_col], errors="coerce")
  df = df.dropna(subset=["DATE_DT"]).copy()
  df["DATE_STR"] = df["DATE_DT"].dt.strftime("%Y-%m-%d")
  df["WEEK"] = get_custom_week(df["DATE_DT"])
  if "TONNAGE" in df.columns:
    df["TOTAL_LOAD"] = pd.to_numeric(df["TONNAGE"], errors="coerce").fillna(0)
  elif "WEIGHT(kg)" in df.columns and "REPS" in df.columns:
    df["TOTAL_LOAD"] = pd.to_numeric(
        df["WEIGHT(kg)"], errors="coerce"
    ) * pd.to_numeric(df["REPS"], errors="coerce")
  else:
    df["TOTAL_LOAD"] = 0
  return df


@st.cache_data(ttl=60)
def load_google_sheet_force():
  sheet_id = "1ib2DrRfODly8HT_V8c2PRNdALYt1_vDCAbvtAK7U1aw"
  esercizi = ["Back Squat", "Front Squat", "Stacco QB"]
  df_list = []

  for ex in esercizi:
    try:
      url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={ex.replace(' ', '%20')}"
      temp = pd.read_csv(url, skiprows=2)
      temp = temp.loc[:, ~temp.columns.str.contains("^Unnamed")]
      temp.columns = temp.columns.astype(str).str.strip()
      if not temp.empty and "Atleta" in temp.columns:
        temp["ESERCIZIO"] = ex
        df_list.append(temp)
    except Exception:
      pass

  if not df_list:
    return pd.DataFrame()

  df = pd.concat(df_list, ignore_index=True)
  df = df[df["Atleta"].notna() & (df["Atleta"] != "Atleta")].copy()

  def clean_num(val):
    if pd.isna(val) or val == "" or val == "-" or "#" in str(val):
      return 0.0
    val_str = str(val).replace(",", ".").strip()
    try:
      return float(val_str)
    except Exception:
      return 0.0

  for col in ["BW", "Peso usato", "Reps", "RIR", "1RM Teorico", "1RM/BW", "1RM Ideale"]:
    if col in df.columns:
      df[col] = df[col].apply(clean_num)
    else:
      df[col] = 0.0

  df["ATHLETE"] = df["Atleta"].map(cognomi_to_full).fillna(df["Atleta"])
  df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")
  return df


# ------------------------------------------------------------------------------
# Registro carichi: scheda "Carichi" del Google Sheet, una riga per ogni serie
# Colonne: Data | Atleta | Esercizio | Peso | Reps | RIR (facoltativa) | Note
# ------------------------------------------------------------------------------
SHEET_ID = "1ib2DrRfODly8HT_V8c2PRNdALYt1_vDCAbvtAK7U1aw"
LOG_SHEET_NAME = "Carichi"
LOG_HEADERS_BY_KEY = {
    "DATA": "Data",
    "ATLETA": "Atleta",
    "ESERCIZIO": "Esercizio",
    "PESO": "Peso",
    "REPS": "Reps",
    "RIR": "RIR",
    "BW": "BW",
    "TARGET": "Target",
    "NOTE": "Note",
}
LOG_HEADERS = list(LOG_HEADERS_BY_KEY.values())
# Esercizi sempre proposti nel menu (oltre a quelli già registrati)
ESERCIZI_BASE = ["Back Squat", "Front Squat", "Stacco QB", "Clean"]
LOG_COLUMN_ALIASES = {
    "DATA": ["data", "date", "giorno"],
    "ATLETA": ["atleta", "athlete", "giocatore", "nome"],
    "ESERCIZIO": ["esercizio", "exercise"],
    "PESO": [
        "peso",
        "kg",
        "carico",
        "peso kg",
        "peso (kg)",
        "weight",
        "weight(kg)",
        "load",
    ],
    "REPS": ["reps", "ripetizioni", "rip", "ripetizioni (reps)"],
    "RIR": ["rir"],
    "BW": ["bw", "peso corporeo", "body weight", "bodyweight", "pc"],
    "TARGET": [
        "target",
        "target xbw",
        "target x bw",
        "target (xbw)",
        "target forza relativa",
    ],
    "NOTE": ["note", "notes"],
}


def _to_float(val):
  if pd.isna(val):
    return float("nan")
  s = re.sub(r"[^0-9.\-]", "", str(val).replace(",", "."))
  if s in ("", "-", "."):
    return float("nan")
  try:
    return float(s)
  except Exception:
    return float("nan")


def _resolve_athlete(name):
  """Riconosce l'atleta anche se scrivi solo il cognome o l'ordine è invertito."""
  s = _slug(name)
  if not s:
    return ""
  for surname, full in SURNAME_TO_PLAYER.items():
    if s == surname or s.startswith(surname) or s.endswith(surname):
      return full
  return str(name).strip()


@st.cache_data(ttl=60)
def load_google_sheet_log():
  sheet_id = _secret("sheet_id") or SHEET_ID
  url = (
      f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
      f"?tqx=out:csv&sheet={quote(LOG_SHEET_NAME)}"
  )
  try:
    raw = pd.read_csv(url)
  except Exception:
    return pd.DataFrame()

  rename = {}
  for col in raw.columns:
    key = str(col).strip().lower()
    for canon, aliases in LOG_COLUMN_ALIASES.items():
      if key in aliases and canon not in rename.values():
        rename[col] = canon
        break
  raw = raw.rename(columns=rename)
  if not {"DATA", "ATLETA", "ESERCIZIO", "PESO", "REPS"}.issubset(raw.columns):
    return pd.DataFrame()

  df = raw[
      [
          c
          for c in [
              "DATA",
              "ATLETA",
              "ESERCIZIO",
              "PESO",
              "REPS",
              "RIR",
              "BW",
              "TARGET",
              "NOTE",
          ]
          if c in raw.columns
      ]
  ].copy()
  for opt in ["RIR", "BW", "TARGET"]:
    if opt not in df.columns:
      df[opt] = float("nan")
  if "NOTE" not in df.columns:
    df["NOTE"] = ""
  df["NOTE"] = df["NOTE"].fillna("").astype(str)

  df["PESO"] = df["PESO"].apply(_to_float)
  df["REPS"] = df["REPS"].apply(_to_float)
  df["RIR"] = df["RIR"].apply(_to_float)
  df["BW"] = df["BW"].apply(_to_float)
  df["BW"] = df["BW"].where(df["BW"] > 0)
  df["TARGET"] = df["TARGET"].apply(_to_float)
  df["TARGET"] = df["TARGET"].where(df["TARGET"] > 0)
  df["DATE_DT"] = parse_dates(df["DATA"])
  df = df.dropna(subset=["DATE_DT", "PESO", "REPS", "ATLETA", "ESERCIZIO"])
  df = df[(df["PESO"] > 0) & (df["REPS"] > 0)].copy()
  if df.empty:
    return pd.DataFrame()

  df["DATE_DT"] = df["DATE_DT"].dt.normalize()
  df["DATE_STR"] = df["DATE_DT"].dt.strftime("%Y-%m-%d")
  df["ATHLETE"] = df["ATLETA"].apply(_resolve_athlete)

  # Esercizi: "clean", "Clean" e "CLEAN " diventano lo stesso esercizio
  ex_raw = (
      df["ESERCIZIO"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
  )
  ex_key = ex_raw.str.lower()
  canon = ex_raw.groupby(ex_key).agg(lambda s: s.value_counts().index[0])
  canon = canon.map(lambda s: s[:1].upper() + s[1:] if s.islower() else s)
  df["ESERCIZIO"] = ex_key.map(canon)
  df = df[df["ESERCIZIO"].str.len() > 0]

  # 1RM stimato (Epley) con RIR: Peso x (1 + (Reps + RIR) / 30)
  reps_eff = df["REPS"] + df["RIR"].fillna(0).clip(lower=0)
  e1rm = df["PESO"].where(reps_eff <= 1, df["PESO"] * (1 + reps_eff / 30))
  df["E1RM"] = e1rm.where(reps_eff <= 10)  # oltre 10 reps la stima non è affidabile
  df["TONNAGE"] = df["PESO"] * df["REPS"]
  df["SERIE"] = (
      df["PESO"].map(lambda v: f"{v:g}")
      + " kg × "
      + df["REPS"].map(lambda v: f"{v:g}")
  )
  return df.reset_index(drop=True)


def _secret(key, default=None):
  try:
    return st.secrets[key]
  except Exception:
    return default


def has_gcp_credentials():
  return (
      _secret("gcp_service_account") is not None
      or bool(_secret("gcp_service_account_json"))
  )


def has_save_backend():
  return bool(_secret("apps_script_url")) or has_gcp_credentials()


def _gcp_info():
  """Credenziali dell'account di servizio Google dai secrets.

  Metodo semplice: gcp_service_account_json = ''' ...intero file JSON... '''
  Metodo alternativo: sezione [gcp_service_account] con i singoli campi.
  """
  raw = _secret("gcp_service_account_json")
  if raw:
    try:
      info = json.loads(raw)
    except Exception:
      raise RuntimeError(
          "gcp_service_account_json non è un JSON valido: incolla l'intero file"
          " scaricato da Google, dalla { iniziale alla } finale."
      )
  else:
    section = _secret("gcp_service_account")
    if section is None:
      return None
    info = dict(section)
  key = str(info.get("private_key", ""))
  if "\\n" in key:  # a capo scritti come testo: li ripristino
    key = key.replace("\\n", "\n")
  if not key.strip().startswith("-----BEGIN"):
    raise RuntimeError(
        "La private_key nei secrets non è completa: deve iniziare con"
        " -----BEGIN PRIVATE KEY----- (è il valore reale del file JSON, non"
        " i puntini di esempio)."
    )
  info["private_key"] = key
  return info


def is_admin():
  """Vero solo se l'URL contiene ?admin=<chiave> uguale a quella nei secrets."""
  token = _secret("admin_token")
  given = st.query_params.get("admin", None)
  if isinstance(given, list):
    given = given[0] if given else None
  if not token or not given:
    return False
  return hmac.compare_digest(str(token).strip(), str(given).strip())


def epley_1rm(kg, reps, rir=0):
  """1RM teorico (Epley): kg x (1 + (reps + RIR) / 30)."""
  reps_eff = float(reps) + max(float(rir or 0), 0.0)
  return float(kg) if reps_eff <= 1 else float(kg) * (1 + reps_eff / 30)


def latest_value(df_src, col):
  """Ultimo valore non vuoto di una colonna (in ordine di data)."""
  if df_src is None or df_src.empty or col not in df_src.columns:
    return None
  s = df_src.dropna(subset=[col]).sort_values("DATE_DT", kind="stable")[col]
  return float(s.iloc[-1]) if len(s) else None


def parse_dates(series):
  """Legge date ISO (2026-10-20) e italiane (20/10/2026) nella stessa colonna."""
  s = series.astype(str).str.strip()
  d = pd.to_datetime(s.str.slice(0, 10), format="%Y-%m-%d", errors="coerce")
  m = d.isna()
  if m.any():
    d = d.fillna(pd.to_datetime(s[m], format="%d/%m/%Y", errors="coerce"))
  m = d.isna()
  if m.any():
    d = d.fillna(pd.to_datetime(s[m], errors="coerce", dayfirst=True))
  return d


def _append_via_apps_script(values):
  """Salva la riga tramite una web app Google Apps Script (gratuita)."""
  url = _secret("apps_script_url")
  key = _secret("apps_script_key")
  if not key:
    raise RuntimeError("Manca apps_script_key nei secrets di Streamlit.")
  r = requests.post(
      str(url).strip(),
      data=json.dumps({"key": str(key), "riga": values}),
      headers={"Content-Type": "text/plain;charset=utf-8"},
      timeout=40,
  )
  try:
    res = r.json()
  except Exception:
    raise RuntimeError(
        f"Risposta inattesa dallo script Google (codice {r.status_code}):"
        " controlla che la web app sia pubblicata con accesso «Chiunque» e"
        " che l'indirizzo finisca con /exec."
    )
  if not res.get("ok"):
    raise RuntimeError(
        f"Lo script ha rifiutato il salvataggio: {res.get('errore', 'errore')}"
    )


def check_apps_script():
  """Prova lo script Google senza scrivere nulla. Ritorna (ok, messaggio)."""
  url = _secret("apps_script_url")
  key = _secret("apps_script_key")
  if not url or not key:
    return False, "Mancano apps_script_url o apps_script_key nei secrets."
  try:
    r = requests.post(
        str(url).strip(),
        data=json.dumps({"key": str(key), "azione": "ping"}),
        headers={"Content-Type": "text/plain;charset=utf-8"},
        timeout=40,
    )
  except Exception as e:
    return False, f"Non riesco a collegarmi allo script ({type(e).__name__})."
  try:
    res = r.json()
  except Exception:
    return False, (
        f"Google risponde (codice {r.status_code}) ma non è lo script."
        " Controlla che l'indirizzo finisca con /exec e che il deployment sia"
        " «Esegui come: Io» e «Chi ha accesso: Chiunque»."
    )
  if not res.get("ok"):
    return False, (
        f"Lo script risponde ma rifiuta: {res.get('errore', 'errore')}."
        " Se dice «chiave non valida», apps_script_key nei secrets deve essere"
        " identica a CHIAVE nello script."
    )
  nome = res.get("foglio", "?")
  fid = str(res.get("id", ""))
  atteso = _secret("sheet_id") or SHEET_ID
  if fid and fid != atteso:
    return False, (
        f"Lo script funziona, ma scrive nel file «{nome}» (ID {fid}) mentre"
        f" l'app legge un altro file (ID {atteso}). Nei secrets scrivi:"
        f' sheet_id = "{fid}"'
    )
  scheda = (
      "presente" if res.get("scheda") else "verrà creata al primo salvataggio"
  )
  return True, (
      f"Lo script funziona e scrive nel file «{nome}», lo stesso che legge"
      f" l'app. Scheda «Carichi»: {scheda}."
  )


def check_read_access():
  """Verifica che l'app riesca a leggere il foglio. Ritorna (ok, messaggio)."""
  sheet_id = _secret("sheet_id") or SHEET_ID
  url = (
      f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
      f"?tqx=out:csv&sheet={quote(LOG_SHEET_NAME)}"
  )
  try:
    r = requests.get(url, headers=REQ_HEADERS, timeout=15)
  except Exception as e:
    return False, f"Non riesco a collegarmi a Google ({type(e).__name__})."
  if r.status_code != 200 or r.text.lstrip().lower().startswith("<"):
    return False, (
        f"L'app non riesce a leggere il file (ID {sheet_id}, codice"
        f" {r.status_code}). In Google Sheet: Condividi → Accesso generale →"
        " «Chiunque abbia il link» → ruolo «Visualizzatore». Controlla anche"
        " che sheet_id nei secrets sia l'ID giusto."
    )
  return True, f"L'app legge il file (ID {sheet_id})."


def append_log_row(values):
  """Aggiunge una riga alla scheda Carichi (la crea se non esiste)."""
  if _secret("apps_script_url"):
    return _append_via_apps_script(values)
  import gspread

  info = _gcp_info()
  if info is None:
    raise RuntimeError(
        "Mancano le credenziali Google nei secrets di Streamlit"
        " (gcp_service_account_json)."
    )
  gc = gspread.service_account_from_dict(info)
  sh = gc.open_by_key(_secret("sheet_id") or SHEET_ID)
  try:
    ws = sh.worksheet(LOG_SHEET_NAME)
  except gspread.WorksheetNotFound:
    ws = sh.add_worksheet(title=LOG_SHEET_NAME, rows=2000, cols=len(LOG_HEADERS))
    ws.append_row(LOG_HEADERS, value_input_option="RAW")

  header = ws.row_values(1)
  canon_cols = []
  for h in header:
    k = str(h).strip().lower()
    canon_cols.append(
        next((c for c, al in LOG_COLUMN_ALIASES.items() if k in al), None)
    )
  # aggiunge in fondo le colonne mancanti (es. BW e Target)
  for key, title in LOG_HEADERS_BY_KEY.items():
    if key not in canon_cols:
      header.append(title)
      canon_cols.append(key)
      ws.update_cell(1, len(header), title)
  row = [values.get(c, "") if c else "" for c in canon_cols]
  ws.append_row(row, value_input_option="RAW")


@st.cache_data(ttl=60)
def diagnose_log_sheet():
  """Spiega perché la scheda Carichi non risulta leggibile."""
  sheet_id = _secret("sheet_id") or SHEET_ID
  url = (
      f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
      f"?tqx=out:csv&sheet={quote(LOG_SHEET_NAME)}"
  )
  try:
    r = requests.get(url, headers=REQ_HEADERS, timeout=10)
  except Exception as e:
    return f"Non riesco a collegarmi a Google ({type(e).__name__})."
  if r.status_code != 200 or r.text.lstrip().lower().startswith("<"):
    return (
        f"Google non restituisce i dati (codice {r.status_code}). Controlla che"
        " il foglio sia condiviso come «Chiunque abbia il link: Visualizzatore»."
    )
  try:
    raw = pd.read_csv(io.StringIO(r.text))
  except Exception as e:
    return f"Il foglio risponde ma non riesco a leggerlo ({type(e).__name__})."

  found = {}
  for col in raw.columns:
    key = str(col).strip().lower()
    for canon, aliases in LOG_COLUMN_ALIASES.items():
      if key in aliases and canon not in found.values():
        found[col] = canon
        break
  missing = [
      c
      for c in ["DATA", "ATLETA", "ESERCIZIO", "PESO", "REPS"]
      if c not in found.values()
  ]
  cols = ", ".join(str(c) for c in raw.columns) or "(nessuna)"
  if missing:
    return (
        f"Il foglio risponde con {len(raw)} righe e queste colonne: {cols}."
        f" Mancano: {', '.join(missing)}. Se queste colonne non sono quelle di"
        " Carichi, la scheda «Carichi» non esiste in questo foglio (Google"
        " mostra la prima scheda al suo posto) oppure le intestazioni non sono"
        " nella riga 1."
    )
  return (
      f"Le colonne sono corrette ({len(raw)} righe), ma nessuna riga è valida:"
      " controlla che Data sia una data (es. 2026-10-20) e che Peso e Reps"
      " siano numeri maggiori di 0."
  )


# ------------------------------------------------------------------------------
# Schede settimanali: ogni settimana 14 file (uno per atleta) con le schede A, B, C
# ------------------------------------------------------------------------------
SCHEDE_INDEX_SHEET = "Settimane"
SESSIONI_LABEL = {
    "A": "A · Forza",
    "B": "B · Forza esplosiva",
    "C": "C · Forza esplosiva",
}
SCHEDA_COLUMN_ALIASES = {
    "EX": ["exercise", "esercizio", "esercizi"],
    "SET": ["set", "serie"],
    "REPS": ["reps", "rep", "ripetizioni"],
    "WEIGHT": ["weight", "peso", "carico", "kg"],
    "RIR": ["rir"],
    "REST": ["rest", "recupero"],
    "NOTE": ["note", "notes"],
}
SCHEDA_META_LABELS = {
    "player": "player",
    "giocatore": "player",
    "atleta": "player",
    "role": "role",
    "ruolo": "role",
    "period": "period",
    "periodo": "period",
}


def _drive_target(text):
  """Da un link o ID Drive: (id, tipo) con tipo = file / folder / auto."""
  s = str(text).strip()
  m = re.search(r"/folders/([A-Za-z0-9_-]{15,})", s)
  if m:
    return m.group(1), "folder"
  m = re.search(r"/d/([A-Za-z0-9_-]{20,})", s)
  if m:
    return m.group(1), "file"
  m = re.search(r"[?&]id=([A-Za-z0-9_-]{20,})", s)
  if m:
    return m.group(1), "auto"
  if re.fullmatch(r"[A-Za-z0-9_-]{25,}", s):
    return s, "auto"
  return None


def _is_empty(v):
  return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""


def _numbers(value):
  """Tutti i numeri scritti in una cella ('6-4-4' -> [6, 4, 4])."""
  if _is_empty(value) or hasattr(value, "year"):  # vuota o data
    return []
  s = str(value).replace(",", ".")
  return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]


def _parse_weights(cell):
  """Pesi di una cella. '1 da 104' = una serie da 104 kg. Percentuali e cm: ignorati."""
  if isinstance(cell, str):
    if re.search(r"%|\bcm\b", cell, flags=re.I):
      return [], None
    m = re.match(r"^\s*(\d+)\s*da\s*(\d+(?:[.,]\d+)?)", cell, flags=re.I)
    if m:
      return [float(m.group(2).replace(",", "."))], int(m.group(1))
  return _numbers(cell), None


def _expand_sets(w_cell, reps_cell, sets_cell, rir_cell):
  """Trasforma le celle di una riga in serie (n, ripetizioni, kg, RIR)."""
  weights, forced_n = _parse_weights(w_cell)
  weights = [w for w in weights if w > 0]
  reps = _numbers(reps_cell)
  if not weights or not reps:
    return []
  sets_list = _numbers(sets_cell)
  n_sets = int(sets_list[0]) if sets_list else 0
  n = forced_n or max(len(weights), len(reps), n_sets)
  n = max(1, min(n, 12))
  rirs = _numbers(rir_cell)
  rir = sum(rirs) / len(rirs) if rirs else 0.0
  out = []
  for i in range(n):
    w = weights[i] if i < len(weights) else weights[-1]
    r = reps[i] if i < len(reps) else reps[-1]
    out.append((i + 1, int(r), float(w), float(rir)))
  return out


def _parse_scheda_df(df):
  """Legge una scheda (tabella senza intestazioni).

  Ritorna (metadati, righe): metadati = player/role/period,
  righe = una per ogni serie con carico.
  """
  meta = {}
  for i in range(min(len(df), 12)):
    row = df.iloc[i].tolist()
    for j, cell in enumerate(row):
      if isinstance(cell, str):
        key = SCHEDA_META_LABELS.get(_slug(cell))
        if key and key not in meta:
          nxt = next((str(c).strip() for c in row[j + 1:] if not _is_empty(c)), None)
          if nxt:
            meta[key] = nxt

  mapping = None
  seduta = 0
  rows = []
  for i in range(len(df)):
    row = df.iloc[i].tolist()
    cells = [str(c).strip().lower() if isinstance(c, str) else "" for c in row]
    if any(c in SCHEDA_COLUMN_ALIASES["EX"] for c in cells) and any(
        c in SCHEDA_COLUMN_ALIASES["REPS"] for c in cells
    ):
      mapping = {}
      for j, c in enumerate(cells):
        for k, aliases in SCHEDA_COLUMN_ALIASES.items():
          if c in aliases and k not in mapping:
            mapping[k] = j
      seduta += 1
      continue
    if mapping is None or "EX" not in mapping:
      continue

    def cell(k):
      idx = mapping.get(k)
      return row[idx] if idx is not None and idx < len(row) else None

    ex = cell("EX")
    if not isinstance(ex, str) or not ex.strip():
      continue
    note = cell("NOTE")
    note = "" if _is_empty(note) else str(note).strip()
    for n, reps, kg, rir in _expand_sets(
        cell("WEIGHT"), cell("REPS"), cell("SET"), cell("RIR")
    ):
      reps_eff = reps + max(rir, 0.0)
      rows.append({
          "SEDUTA": seduta,
          "ESERCIZIO": " ".join(ex.split()),
          "SET_N": n,
          "REPS": reps,
          "PESO": kg,
          "RIR": rir,
          "E1RM": epley_1rm(kg, reps, rir) if reps_eff <= 10 else float("nan"),
          "TONNAGE": kg * reps,
          "NOTE": note,
      })
  return meta, rows


def lift_kind(name):
  """Riconosce i tre alzati con 1RM (Epley), in italiano e in inglese.

  Ritorna "Back Squat", "Front Squat", "Stacco Quadrabar" oppure None.
  Esempi: Squat frontale, Trap Bar Deadlift, Hex Bar Deadlift, Stacco QB.
  """
  toks = _tokens(name)
  compact = re.sub(r"[^a-z0-9]", "", _ascii_lower(name))

  # Squat (back o front), escludendo le varianti che non sono lo squat classico
  no_squat = toks & {
      "split", "bulgarian", "bulgaro", "goblet", "overhead", "jump", "salto",
  }
  if not no_squat:
    if "frontsquat" in compact or (
        "squat" in compact and toks & {"front", "frontale"}
    ):
      return "Front Squat"
    if "backsquat" in compact or (
        "squat" in compact and toks & {"back", "dietro", "posteriore"}
    ):
      return "Back Squat"

  # Stacco con quadrabar / trap bar (non gli stacchi rumeni, né i salti)
  is_deadlift = "stacco" in compact or "deadlift" in compact or "dl" in toks
  has_bar = any(
      k in compact for k in ("trapbar", "hexbar", "quadrabar", "quadbar")
  ) or bool(toks & {"qb", "tb", "hex", "trap"})
  if (
      is_deadlift
      and has_bar
      and not (
          toks
          & {"romanian", "rumeno", "rdl", "stiff", "single", "jump", "salto"}
      )
  ):
    return "Stacco Quadrabar"
  return None


def uses_e1rm(name):
  return lift_kind(name) is not None


def _fmt_kg(w):
  return f"{float(w):g}".replace(".", ",")


def _fmt_set(w, reps):
  return f"{_fmt_kg(w)} kg × {int(reps)}"


def _fetch_workbook(file_id):
  """Scarica un intero file Google Sheet (tutte le schede) in un colpo solo."""
  url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
  r = requests.get(url, headers=REQ_HEADERS, timeout=90)
  if r.status_code != 200 or r.content[:2] != b"PK":
    raise RuntimeError(
        f"codice {r.status_code}: il file non è condiviso come «Chiunque abbia"
        " il link → Visualizzatore» oppure non è un Google Sheet"
    )
  return pd.read_excel(io.BytesIO(r.content), sheet_name=None, header=None)


def _safe_fetch(file_id):
  try:
    return _fetch_workbook(file_id), None
  except ImportError:
    return None, "manca la libreria openpyxl (aggiungila al requirements.txt)"
  except Exception as e:
    return None, f"{type(e).__name__}: {e}"


def _looks_like_xlsx(file_id):
  """Vero se l'ID è un Google Sheet scaricabile (controlla solo i primi byte)."""
  try:
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    r = requests.get(url, headers=REQ_HEADERS, timeout=30, stream=True)
    head = next(r.iter_content(2), b"")
    r.close()
    return r.status_code == 200 and head == b"PK"
  except Exception:
    return False


def _list_drive_folder(folder_id):
  """Elementi di una cartella Drive condivisa con «Chiunque abbia il link»."""
  page = _fetch_html(
      f"https://drive.google.com/embeddedfolderview?id={folder_id}", timeout=30
  )
  found = {}

  def add(item_id, kind):
    if item_id and item_id != folder_id and (
        item_id not in found or found[item_id] == "auto"
    ):
      found[item_id] = kind

  for href in re.findall(r'href="([^"]+)"', page):
    t = _drive_target(html_lib.unescape(href))
    if t:
      add(*t)
  for m in re.finditer(r'(?:data-id="|id="entry-)([A-Za-z0-9_-]{20,})"', page):
    add(m.group(1), "auto")
  return list(found.items())


def _expand_sources(sources):
  """Da link di file e/o cartelle all'elenco di tutti i file da leggere."""
  files, notes = [], []
  seen_files, seen_folders = set(), set()
  queue = [(i, k, 0) for i, k in sources]
  while queue and len(files) < 600:
    item_id, kind, depth = queue.pop(0)
    if kind == "auto":
      kind = "file" if _looks_like_xlsx(item_id) else "folder"
    if kind == "file":
      if item_id not in seen_files:
        seen_files.add(item_id)
        files.append(item_id)
      continue
    if item_id in seen_folders or depth > 3:
      continue
    seen_folders.add(item_id)
    items = _list_drive_folder(item_id)
    notes.append(f"cartella {item_id[:8]}…: {len(items)} elementi trovati")
    for child_id, child_kind in items:
      queue.append((child_id, child_kind, depth + 1))
  return files, notes


@st.cache_data(ttl=120, show_spinner=False)
def load_schede_index():
  """Link dei file o delle cartelle: scheda «Settimane» del foglio + secrets."""
  targets = []
  sheet_id = _secret("sheet_id") or SHEET_ID
  url = (
      f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
      f"?tqx=out:csv&sheet={quote(SCHEDE_INDEX_SHEET)}"
  )
  try:
    raw = pd.read_csv(url, header=None, dtype=str)
    for v in raw.values.ravel():
      if isinstance(v, str):
        t = _drive_target(v)
        if t:
          targets.append(t)
  except Exception:
    pass
  extra = _secret("schede_urls")
  if extra:
    items = extra if isinstance(extra, (list, tuple)) else str(extra).splitlines()
    for item in items:
      t = _drive_target(item)
      if t:
        targets.append(t)
  seen, out = set(), []
  for t in targets:
    if t[0] not in seen:
      seen.add(t[0])
      out.append(t)
  return tuple(out)


@st.cache_data(ttl=300, show_spinner="Cerco i file delle schede…")
def list_schede_files(sources):
  files, notes = _expand_sources(sources)
  return tuple(files), tuple(notes)


@st.cache_resource
def _schede_file_cache():
  return {}


def _load_file_cached(file_id, cache):
  """Scarica e legge un file; le settimane vecchie restano in memoria più a lungo."""
  now = time.time()
  weeks = [e["week"] for e in cache.values() if e.get("week") is not None]
  newest = max(weeks) if weeks else None
  e = cache.get(file_id)
  if e:
    if e.get("error"):
      ttl = 600
    elif e.get("week") is not None and newest is not None and e["week"] <= newest - 2:
      ttl = 21600
    else:
      ttl = 300
    if now - e["t"] < ttl:
      return e
  book, err = _safe_fetch(file_id)
  if err:
    e = {"t": now, "week": None, "tabs": [], "error": err}
  else:
    tabs, file_week = [], None
    for tab, df in book.items():
      meta, srows = _parse_scheda_df(df)
      m = re.search(r"(?:week|settimana)\s*(\d+)", meta.get("period", ""), flags=re.I)
      wk = int(m.group(1)) if m else None
      if file_week is None and wk is not None:
        file_week = wk
      tabs.append({"tab": str(tab).strip(), "meta": meta, "rows": srows, "week": wk})
    e = {"t": now, "week": file_week, "tabs": tabs, "error": None}
  cache[file_id] = e
  return e


@st.cache_data(ttl=120, show_spinner="Leggo le schede settimanali…")
def load_schede_settimanali(file_ids):
  """Legge tutti i file. Ritorna (serie, riepilogo file e schede)."""
  cache = _schede_file_cache()
  with ThreadPoolExecutor(max_workers=6) as pool:
    entries = list(pool.map(lambda fid: _load_file_cached(fid, cache), file_ids))

  rows, info = [], []
  for order, (fid, e) in enumerate(zip(file_ids, entries)):
    short = fid[:8] + "…"
    if e["error"]:
      info.append({"File": short, "Scheda": "—", "Atleta": "—", "Periodo": "—",
                   "Serie lette": 0, "Esito": e["error"]})
      continue
    for t in e["tabs"]:
      meta = t["meta"]
      period = meta.get("period", "")
      week = t["week"] or e["week"] or (order + 1)
      fase = re.sub(r"(?i)^\s*(?:week|settimana)\s*\d+\s*[-–:]*\s*", "", period).strip()
      athlete = _resolve_athlete(meta.get("player") or t["tab"])
      for r in t["rows"]:
        rows.append({**r, "SETTIMANA": week, "FASE": fase, "ATHLETE": athlete,
                     "SESSIONE": t["tab"]})
      info.append({
          "File": short,
          "Scheda": t["tab"],
          "Atleta": athlete,
          "Periodo": period or "—",
          "Serie lette": len(t["rows"]),
          "Esito": "ok" if t["rows"] else "nessun carico trovato",
      })
  df_all = pd.DataFrame(rows)
  if not df_all.empty:
    key = df_all["ESERCIZIO"].str.lower()
    canon = df_all["ESERCIZIO"].groupby(key).agg(lambda s: s.value_counts().index[0])
    df_all["ESERCIZIO"] = key.map(canon)
    df_all["SETTIMANA"] = df_all["SETTIMANA"].astype(int)
    # Gli alzati principali hanno sempre lo stesso nome, in italiano o in inglese
    df_all["ESERCIZIO"] = df_all["ESERCIZIO"].map(lambda n: lift_kind(n) or n)
    # 1RM (Epley) solo per Back Squat, Front Squat e Stacco quadrabar
    df_all.loc[~df_all["ESERCIZIO"].map(uses_e1rm), "E1RM"] = float("nan")
  return df_all, pd.DataFrame(info)


# Controllo automatico dei file: ogni 30 secondi verifica se i CSV sono
# cambiati (nuovi file o file modificati) e, in caso, riesegue tutta l'app.
@st.fragment(run_every=30)
def watch_data_folder():
  current = get_files_signature()
  if "files_sig" not in st.session_state:
    st.session_state.files_sig = current
  elif st.session_state.files_sig != current:
    st.session_state.files_sig = current
    st.rerun()


watch_data_folder()


# ==============================================================================
# SCHERMATA 1: HOME PAGE
# ==============================================================================
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

  col_card1, col_card2 = st.columns(2)
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

# ==============================================================================
# SCHERMATA 2: MODULO DATAJUMP
# ==============================================================================
elif st.session_state.page == "datajump":
  col_h1, col_h2 = st.columns([8, 2])
  with col_h1:
    st.markdown("### 🚀 **DataJump** — Monitoraggio Salti & Elevazione")
  with col_h2:
    if st.button("🏠 Torna alla Home", use_container_width=True):
      st.session_state.page = "home"
      st.rerun()

  if allowed_athletes == "ALL":
    st.sidebar.success("🔓 Visualizzazione: Roster Completo")
  else:
    st.sidebar.success(f"🔓 Visualizzazione Dedicata: {allowed_athletes[0]}")

  df_jump = load_jump_data(get_files_signature())
  if df_jump.empty:
    st.warning("⚠️ Nessun file CSV relativo ai salti trovato.")
    st.stop()

  st.sidebar.caption(
      f"📁 {len(get_csv_files())} file CSV trovati · "
      f"{df_jump['DATE_STR'].nunique()} sedute caricate"
  )

  if allowed_athletes != "ALL":
    df_jump = df_jump[df_jump["ATHLETE"].isin(allowed_athletes)]

  st.sidebar.divider()
  st.sidebar.header("🔍 Filtri Selezione & Confronto")
  ruoli_list = sorted(list(set(df_jump["ROLE"].unique())))
  selected_roles = st.sidebar.multiselect("Filtra per Ruolo", ruoli_list)
  df_f = df_jump.copy()
  if selected_roles:
    df_f = df_f[df_f["ROLE"].isin(selected_roles)]

  giocatori_list = sorted(df_f["ATHLETE"].unique())
  selected_players = st.sidebar.multiselect(
      "Seleziona Giocatori da Analizzare / Confrontare", giocatori_list
  )
  if selected_players:
    df_f = df_f[df_f["ATHLETE"].isin(selected_players)]

  # Base per il confronto tra settimane: filtri Ruolo e Giocatori applicati,
  # filtri Settimane e Date Sedute esclusi
  df_base = df_f.copy()

  unique_weeks = sorted(
      [w for w in df_f["WEEK"].unique() if pd.notna(w)],
      key=extract_week_num,
      reverse=True,
  )
  selected_weeks = st.sidebar.multiselect(
      "Settimane di Lavoro", unique_weeks
  )
  if selected_weeks:
    df_f = df_f[df_f["WEEK"].isin(selected_weeks)]

  sessioni_list = sorted(
      [d for d in df_f["DATE_STR"].unique() if pd.notna(d)], reverse=True
  )
  selected_sessions = st.sidebar.multiselect("Date Sedute", sessioni_list)
  if selected_sessions:
    df_f = df_f[df_f["DATE_STR"].isin(selected_sessions)]

  single_player_target = (
      selected_players[0]
      if selected_players and len(selected_players) == 1
      else (allowed_athletes[0] if allowed_athletes != "ALL" else None)
  )

  if single_player_target:
    p = single_player_target
    role_val = ruoli_dict.get(p, "Atleta")
    details = player_info.get(p, {})
    bio_val = details.get("bio", "Cuneo Volley Prima Squadra")

    # Link alla scheda del giocatore sul sito della Lega Volley
    lega_key = load_lega_player_ids().get(p)
    if lega_key:
      link_val = f"{LEGA_BASE}/player/{lega_key}"
    else:
      link_val = (
          f"{LEGA_BASE}/ricerca/?Search={quote(p.split()[-1])}"
          "&TipoOgg=ATL&FindAll=0"
      )

    # Foto presa dal sito (si aggiorna da sola ogni 10 minuti)
    photo_uri = get_player_photo(p)
    if photo_uri:
      photo_html = (
          f'<img src="{photo_uri}" alt="{html_lib.escape(p)}" '
          'style="width:130px;height:130px;object-fit:cover;'
          "object-position:top;border-radius:50%;"
          'border:3px solid #2563eb;flex-shrink:0;">'
      )
    else:
      photo_html = '<div style="font-size:3.2rem;flex-shrink:0;">🛡️</div>'

    card_html = (
        '<div class="player-card" style="display:flex;align-items:center;'
        'gap:24px;flex-wrap:wrap;">'
        f"{photo_html}"
        "<div>"
        f'<div class="player-title">{html_lib.escape(p)}</div>'
        f'<div class="player-role">Ruolo: {html_lib.escape(role_val)}</div>'
        '<p style="color:#475569;margin-top:8px;margin-bottom:12px;">'
        f"{html_lib.escape(bio_val)}</p>"
        f'<a href="{link_val}" target="_blank" '
        'style="color:#2563eb;text-decoration:none;font-weight:600;">'
        "🔗 Vai alla scheda ufficiale su Lega Pallavolo Serie A &rarr;</a>"
        "</div></div>"
    )
    st.markdown(card_html, unsafe_allow_html=True)

  daily_summary = (
      df_f.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"])
      .agg(
          SALTI_GIORNO=("JUMP HEIGHT(cm)", "count"),
          MAX_GIORNO=("JUMP HEIGHT(cm)", "max"),
          MEDIA_GIORNO=("JUMP HEIGHT(cm)", "mean"),
          IS_MATCH=("IS_MATCH", "max"),
      )
      .reset_index()
  )

  weekly_summary = (
      df_f.groupby(["ATHLETE", "ROLE", "WEEK"])
      .agg(
          SALTI_SETTIMANA=("JUMP HEIGHT(cm)", "count"),
          MAX_SETTIMANA=("JUMP HEIGHT(cm)", "max"),
          MEDIA_SETTIMANA=("JUMP HEIGHT(cm)", "mean"),
      )
      .reset_index()
  )

  c1, c2, c3, c4 = st.columns(4)
  c1.metric(
      "Totale Salti",
      f"{daily_summary['SALTI_GIORNO'].sum() if not daily_summary.empty else 0}",
  )
  c2.metric(
      "Salto Max",
      f"{daily_summary['MAX_GIORNO'].max() if not daily_summary.empty else 0:.1f} cm",
  )
  c3.metric(
      "Media Salti",
      f"{daily_summary['MEDIA_GIORNO'].mean() if not daily_summary.empty else 0:.1f} cm",
  )
  c4.metric(
      "Giocatori Monitorati",
      f"{len(df_f['ATHLETE'].unique()) if not df_f.empty else 0}",
  )

  st.divider()

  tab1, tab2, tab3, tab4, tab5 = st.tabs([
      "📊 Andamento Giornaliero",
      "🗓️ Andamento Settimanale",
      "⚔️ Confronto Giocatori",
      "🎯 Distribuzione Fasce",
      "🆚 Confronto Settimane",
  ])

  with tab1:
    if not daily_summary.empty:
      st.markdown(
          "##### 🔵 Volume Salti per Data e Giocatore — ultime 7 sedute"
      )
      # Solo le 7 date più recenti (tra quelle che passano i filtri)
      ultime_date = sorted(daily_summary["DATE_STR"].unique())[-7:]
      daily_recent = daily_summary[daily_summary["DATE_STR"].isin(ultime_date)]
      match_dates = daily_recent[daily_recent["IS_MATCH"].astype(bool)][
          ["DATE_STR"]
      ].drop_duplicates()
      bars1 = (
          alt.Chart(daily_recent)
          .mark_bar()
          .encode(
              x=alt.X("DATE_STR:N", title="Data Seduta"),
              y=alt.Y("SALTI_GIORNO:Q", title="Nr. Salti"),
              color=alt.Color("ATHLETE:N", title="Giocatore"),
              tooltip=["DATE_STR", "ATHLETE", "SALTI_GIORNO", "MAX_GIORNO"],
          )
      )
      if match_dates.empty:
        chart1 = bars1.properties(height=380)
      else:
        match_bg = (
            alt.Chart(match_dates)
            .mark_rect(color="#f97316", opacity=0.2)
            .encode(
                x=alt.X("DATE_STR:N", title="Data Seduta"),
                y=alt.value(0),
                y2=alt.value(380),
            )
        )
        chart1 = alt.layer(match_bg, bars1).properties(height=380)
      st.altair_chart(chart1, use_container_width=True)
      st.caption("🟠 Colonna / pallino arancione = giorno di partita")

      st.markdown("##### 🚀 Salto Max (cm) — ultime 7 sedute")
      line2 = (
          alt.Chart(daily_recent)
          .mark_line(point=True)
          .encode(
              x=alt.X("DATE_STR:N", title="Data Seduta"),
              y=alt.Y("MAX_GIORNO:Q", title="Salto Max (cm)"),
              color=alt.Color("ATHLETE:N", title="Giocatore"),
              tooltip=["DATE_STR", "ATHLETE", "MAX_GIORNO"],
          )
      )
      match_pts = daily_recent[daily_recent["IS_MATCH"].astype(bool)]
      if match_pts.empty:
        chart2 = line2.properties(height=380)
      else:
        match_dots = (
            alt.Chart(match_pts)
            .mark_point(filled=True, color="#f97316", size=260)
            .encode(
                x=alt.X("DATE_STR:N", title="Data Seduta"),
                y=alt.Y("MAX_GIORNO:Q", title="Salto Max (cm)"),
                tooltip=["DATE_STR", "ATHLETE", "MAX_GIORNO"],
            )
        )
        chart2 = alt.layer(line2, match_dots).properties(height=380)
      st.altair_chart(chart2, use_container_width=True)

      if single_player_target:
        st.divider()
        st.markdown(
            f"##### 📈 Andamento dei Salti all'Interno delle Sessioni —"
            f" {single_player_target}"
        )
        st.info(
            "I grafici seguenti mostrano l'altezza dei singoli salti in ordine"
            " cronologico per ciascuna seduta di allenamento dell'atleta,"
            " in base all'orario in cui sono stati eseguiti."
        )

        df_session_seq = df_f.copy()
        # Ordinamento stabile: a parità di orario si mantiene l'ordine del file
        df_session_seq = df_session_seq.sort_values(
            by=["DATETIME"], kind="stable"
        )
        df_session_seq["NUM_SALTO"] = df_session_seq.groupby(
            ["DATE_STR", "ATHLETE"]
        ).cumcount() + 1

        if not df_session_seq.empty and not df_session_seq["HAS_TIME"].any():
          st.warning(
              "Nei file CSV non trovo l'orario dei salti (né dentro la colonna"
              " DATE né in una colonna TIME / ORA / ORARIO / HOUR): sull'asse"
              " orizzontale mostro quindi il numero progressivo del salto."
          )

        # Dalla seduta più recente alla meno recente
        date_disponibili = sorted(
            df_session_seq["DATE_STR"].unique(), reverse=True
        )

        if not date_disponibili:
          st.warning("Nessuna sessione trovata con i filtri attuali.")
        else:
          for data_seduta in date_disponibili:
            df_data_sub = df_session_seq[
                df_session_seq["DATE_STR"] == data_seduta
            ]
            has_time = bool(df_data_sub["HAS_TIME"].any())

            is_match_day = data_seduta in MATCH_DAYS
            st.markdown(
                f"**📅 Seduta del: {data_seduta}**"
                + (" &nbsp; 🟠 **Match day**" if is_match_day else "")
            )

            if has_time:
              x_enc = alt.X(
                  "DATETIME:T",
                  title="Orario del salto",
                  axis=alt.Axis(format="%H:%M", labelAngle=0),
              )
              tooltip_enc = [
                  "ATHLETE",
                  alt.Tooltip(
                      "DATETIME:T", title="Orario", format="%H:%M:%S"
                  ),
                  alt.Tooltip("NUM_SALTO:Q", title="N° salto"),
                  "JUMP HEIGHT(cm)",
                  "JUMP_BAND",
              ]
            else:
              x_enc = alt.X(
                  "NUM_SALTO:Q",
                  title="Progressione Salti nella Seduta",
              )
              tooltip_enc = [
                  "ATHLETE",
                  "NUM_SALTO",
                  "JUMP HEIGHT(cm)",
                  "JUMP_BAND",
              ]

            chart_intra = (
                alt.Chart(df_data_sub)
                .mark_line(
                    point=True,
                    strokeWidth=2,
                    color="#f97316" if is_match_day else "#2563eb",
                )
                .encode(
                    x=x_enc,
                    y=alt.Y(
                        "JUMP HEIGHT(cm):Q", title="Altezza Salto (cm)"
                    ),
                    order=alt.Order("NUM_SALTO:Q"),
                    tooltip=tooltip_enc,
                )
                .properties(height=300, width="container")
            )
            st.altair_chart(chart_intra, use_container_width=True)

  with tab2:
    if not weekly_summary.empty:
      st.markdown("##### 🔵 Volume Salti Settimanali")
      chart_w = (
          alt.Chart(weekly_summary)
          .mark_bar()
          .encode(
              x=alt.X("WEEK:N", title="Settimana"),
              y=alt.Y("SALTI_SETTIMANA:Q", title="Nr. Salti"),
              color=alt.Color("ATHLETE:N", title="Giocatore"),
              tooltip=["WEEK", "ATHLETE", "SALTI_SETTIMANA"],
          )
          .properties(height=380)
      )
      st.altair_chart(chart_w, use_container_width=True)

  with tab3:
    if not df_f.empty:
      comp_df = (
          df_f.groupby(["ATHLETE", "ROLE"])
          .agg(
              TOT_SALTI=("JUMP HEIGHT(cm)", "count"),
              MAX_SALTO=("JUMP HEIGHT(cm)", "max"),
              MEDIA_SALTO=("JUMP HEIGHT(cm)", "mean"),
          )
          .reset_index()
      )
      col_a, col_b = st.columns(2)
      with col_a:
        st.write("**Totale Salti per Giocatore**")
        st.altair_chart(
            alt.Chart(comp_df)
            .mark_bar(color="#2563eb")
            .encode(
                x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                y=alt.Y("TOT_SALTI:Q", title="Totale Salti"),
                tooltip=["ATHLETE", "TOT_SALTI"],
            )
            .properties(height=350),
            use_container_width=True,
        )
      with col_b:
        st.write("**Salto Max (cm) per Giocatore**")
        st.altair_chart(
            alt.Chart(comp_df)
            .mark_bar(color="#f97316")
            .encode(
                x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                y=alt.Y("MAX_SALTO:Q", title="Salto Max (cm)"),
                tooltip=["ATHLETE", "MAX_SALTO"],
            )
            .properties(height=350),
            use_container_width=True,
        )

  with tab4:
    if not df_f.empty:
      order_list = [
          "JUMPS < 30",
          "JUMPS 30-50",
          "JUMPS 50-60",
          "JUMPS 60-70",
          "JUMPS > 70",
      ]
      band_comp = (
          df_f.groupby(["JUMP_BAND", "ATHLETE"])
          .size()
          .reset_index(name="Numero Salti")
      )
      chart_b = (
          alt.Chart(band_comp)
          .mark_bar()
          .encode(
              x=alt.X("JUMP_BAND:N", sort=order_list, title="Fascia"),
              y=alt.Y("Numero Salti:Q"),
              color=alt.Color("ATHLETE:N", title="Giocatore"),
              tooltip=["JUMP_BAND", "ATHLETE", "Numero Salti"],
          )
          .properties(height=400)
      )
      st.altair_chart(chart_b, use_container_width=True)

  with tab5:
    st.markdown("##### 🆚 Confronto tra due settimane di lavoro")
    st.caption(
        "Usa i filtri Ruolo e Giocatori della barra laterale; ignora i filtri"
        " Settimane e Date Sedute, così puoi scegliere qui le due settimane."
    )
    settimane_cmp = sorted(
        [w for w in df_base["WEEK"].unique() if pd.notna(w)],
        key=extract_week_num,
        reverse=True,
    )
    if len(settimane_cmp) < 2:
      st.info("Servono dati di almeno due settimane per fare il confronto.")
    else:
      col_wa, col_wb = st.columns(2)
      with col_wa:
        week_a = st.selectbox(
            "Settimana A (riferimento)",
            settimane_cmp,
            index=1,
            key="cmp_week_a",
        )
      with col_wb:
        week_b = st.selectbox(
            "Settimana B (da confrontare)",
            settimane_cmp,
            index=0,
            key="cmp_week_b",
        )

      if week_a == week_b:
        st.warning("Scegli due settimane diverse per il confronto.")
      else:
        df_a = df_base[df_base["WEEK"] == week_a]
        df_b = df_base[df_base["WEEK"] == week_b]

        def week_stats(d):
          if d.empty:
            return {"salti": 0, "max": 0.0, "media": 0.0, "sedute": 0}
          h = d["JUMP HEIGHT(cm)"]
          return {
              "salti": int(h.count()),
              "max": float(h.max()),
              "media": float(h.mean()),
              "sedute": int(d["DATE_STR"].nunique()),
          }

        sa, sb = week_stats(df_a), week_stats(df_b)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            f"Totale Salti — {week_b}",
            f"{sb['salti']}",
            f"{sb['salti'] - sa['salti']:+d} vs {week_a}",
        )
        m2.metric(
            f"Salto Max — {week_b}",
            f"{sb['max']:.1f} cm",
            f"{sb['max'] - sa['max']:+.1f} cm",
        )
        m3.metric(
            f"Media Salti — {week_b}",
            f"{sb['media']:.1f} cm",
            f"{sb['media'] - sa['media']:+.1f} cm",
        )
        m4.metric(
            f"Sedute — {week_b}",
            f"{sb['sedute']}",
            f"{sb['sedute'] - sa['sedute']:+d}",
        )
        st.caption(
            f"{week_a}: {sa['salti']} salti · max {sa['max']:.1f} cm · media"
            f" {sa['media']:.1f} cm · {sa['sedute']} sedute"
        )

        cmp_df = pd.concat(
            [df_a.assign(SETTIMANA=week_a), df_b.assign(SETTIMANA=week_b)],
            ignore_index=True,
        )
        cmp_df["GIORNO"] = cmp_df["DATE_DT"].dt.dayofweek.map(
            lambda i: GIORNI[int(i)]
        )
        cmp_daily = (
            cmp_df.groupby(["SETTIMANA", "GIORNO", "DATE_STR"])
            .agg(
                SALTI=("JUMP HEIGHT(cm)", "count"),
                SALTO_MAX=("JUMP HEIGHT(cm)", "max"),
                SALTO_MEDIO=("JUMP HEIGHT(cm)", "mean"),
                IS_MATCH=("IS_MATCH", "max"),
            )
            .reset_index()
        )
        cmp_daily["IS_MATCH"] = cmp_daily["IS_MATCH"].astype(bool)

        week_color = alt.Color(
            "SETTIMANA:N",
            title="Settimana",
            scale=alt.Scale(
                domain=[week_a, week_b], range=["#94a3b8", "#2563eb"]
            ),
        )

        def cmp_bar(value_col, title):
          bars = (
              alt.Chart(cmp_daily)
              .mark_bar()
              .encode(
                  x=alt.X("GIORNO:N", sort=GIORNI, title="Giorno"),
                  xOffset=alt.XOffset("SETTIMANA:N"),
                  y=alt.Y(f"{value_col}:Q", title=title),
                  color=week_color,
                  tooltip=[
                      "SETTIMANA",
                      "GIORNO",
                      "DATE_STR",
                      alt.Tooltip("SALTI:Q", title="Salti"),
                      alt.Tooltip(
                          "SALTO_MAX:Q", title="Max (cm)", format=".1f"
                      ),
                      alt.Tooltip(
                          "SALTO_MEDIO:Q", title="Media (cm)", format=".1f"
                      ),
                  ],
              )
          )
          match_df = cmp_daily[cmp_daily["IS_MATCH"]]
          if match_df.empty:
            return bars.properties(height=340)
          dots = (
              alt.Chart(match_df)
              .mark_point(filled=True, color="#f97316", size=150)
              .encode(
                  x=alt.X("GIORNO:N", sort=GIORNI),
                  xOffset=alt.XOffset("SETTIMANA:N"),
                  y=f"{value_col}:Q",
              )
          )
          return alt.layer(bars, dots).properties(height=340)

        cc1, cc2 = st.columns(2)
        with cc1:
          st.write("**Volume Salti per Giorno**")
          st.altair_chart(
              cmp_bar("SALTI", "Nr. Salti"), use_container_width=True
          )
        with cc2:
          st.write("**Salto Max (cm) per Giorno**")
          st.altair_chart(
              cmp_bar("SALTO_MAX", "Salto Max (cm)"),
              use_container_width=True,
          )
        st.caption("🟠 Pallino arancione = giorno di partita")

        band_cmp = (
            cmp_df.groupby(["SETTIMANA", "JUMP_BAND"])
            .size()
            .reset_index(name="N")
        )
        band_cmp["PERC"] = (
            band_cmp["N"]
            / band_cmp.groupby("SETTIMANA")["N"].transform("sum")
            * 100
        )
        st.write("**Distribuzione Fasce (% sui salti della settimana)**")
        chart_band_cmp = (
            alt.Chart(band_cmp)
            .mark_bar()
            .encode(
                x=alt.X("JUMP_BAND:N", sort=BAND_ORDER, title="Fascia"),
                xOffset=alt.XOffset("SETTIMANA:N"),
                y=alt.Y("PERC:Q", title="% dei salti"),
                color=week_color,
                tooltip=[
                    "SETTIMANA",
                    "JUMP_BAND",
                    alt.Tooltip("N:Q", title="Nr. salti"),
                    alt.Tooltip("PERC:Q", title="%", format=".1f"),
                ],
            )
            .properties(height=340)
        )
        st.altair_chart(chart_band_cmp, use_container_width=True)

        st.write("**Dettaglio per Giorno**")
        detail = cmp_daily.copy()
        detail["PARTITA"] = detail["IS_MATCH"].map(
            {True: "🟠 Match day", False: ""}
        )
        detail["SALTO_MAX"] = detail["SALTO_MAX"].round(1)
        detail["SALTO_MEDIO"] = detail["SALTO_MEDIO"].round(1)
        detail["_g"] = detail["GIORNO"].map(
            {g: i for i, g in enumerate(GIORNI)}
        )
        detail["_w"] = detail["SETTIMANA"].map({week_a: 0, week_b: 1})
        detail = detail.sort_values(["_g", "_w"]).drop(
            columns=["_g", "_w", "IS_MATCH"]
        )
        st.dataframe(
            detail.rename(
                columns={
                    "SETTIMANA": "Settimana",
                    "GIORNO": "Giorno",
                    "DATE_STR": "Data",
                    "SALTI": "Salti",
                    "SALTO_MAX": "Salto max (cm)",
                    "SALTO_MEDIO": "Media (cm)",
                    "PARTITA": "Partita",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        if cmp_df["ATHLETE"].nunique() > 1:
          st.write("**Confronto per Giocatore**")
          by_player = (
              cmp_df.groupby(["ATHLETE", "SETTIMANA"])
              .agg(
                  SALTI=("JUMP HEIGHT(cm)", "count"),
                  MAX=("JUMP HEIGHT(cm)", "max"),
                  MEDIA=("JUMP HEIGHT(cm)", "mean"),
              )
              .reset_index()
          )
          wide = by_player.pivot(
              index="ATHLETE",
              columns="SETTIMANA",
              values=["SALTI", "MAX", "MEDIA"],
          )
          salti_a = wide[("SALTI", week_a)].fillna(0).astype(int)
          salti_b = wide[("SALTI", week_b)].fillna(0).astype(int)
          player_table = pd.DataFrame({
              f"Salti {week_a}": salti_a,
              f"Salti {week_b}": salti_b,
              "Δ Salti": salti_b - salti_a,
              f"Media {week_a} (cm)": wide[("MEDIA", week_a)].round(1),
              f"Media {week_b} (cm)": wide[("MEDIA", week_b)].round(1),
              "Δ Media (cm)": (
                  wide[("MEDIA", week_b)] - wide[("MEDIA", week_a)]
              ).round(1),
              f"Max {week_a} (cm)": wide[("MAX", week_a)].round(1),
              f"Max {week_b} (cm)": wide[("MAX", week_b)].round(1),
          }).reset_index()
          st.dataframe(
              player_table, use_container_width=True, hide_index=True
          )

# ==============================================================================
# SCHERMATA 3: MODULO DATALOAD
# ==============================================================================
elif st.session_state.page == "dataload":
  col_h1, col_h2 = st.columns([8, 2])
  with col_h1:
    st.markdown("### 🏋️‍♂️ **DataLoad** — Carichi, Massimali & Valutazione Forza")
  with col_h2:
    if st.button("🏠 Torna alla Home", use_container_width=True):
      st.session_state.page = "home"
      st.rerun()

  if allowed_athletes == "ALL":
    st.sidebar.success("🔓 Visualizzazione: Roster Completo")
  else:
    st.sidebar.success(f"🔓 Visualizzazione Dedicata: {allowed_athletes[0]}")

  df_load = load_load_data(get_files_signature())
  df_force = load_google_sheet_force()
  df_log = load_google_sheet_log()

  if allowed_athletes != "ALL":
    if not df_load.empty:
      df_load = df_load[df_load["ATHLETE"].isin(allowed_athletes)]
    if not df_force.empty:
      df_force = df_force[df_force["ATHLETE"].isin(allowed_athletes)]
    if not df_log.empty:
      df_log = df_log[df_log["ATHLETE"].isin(allowed_athletes)]

  st.sidebar.divider()
  st.sidebar.header("🔍 Filtri Selezione & Confronto")

  admin_mode = is_admin()
  if admin_mode:
    st.sidebar.success("✍️ Modalità modifica attiva")
  elif st.query_params.get("admin"):
    if _secret("admin_token") is None:
      st.sidebar.warning(
          "Modalità modifica non attiva: nei secrets dell'app non trovo"
          " `admin_token` (secrets non salvati, app non riavviata, oppure"
          " errore di scrittura nel file dei secrets)."
      )
    else:
      st.sidebar.warning(
          "Modalità modifica non attiva: la chiave nel link non coincide con"
          " `admin_token` dei secrets."
      )

  tab_labels = [
      "📋 Schede Settimanali",
      "📈 Carichi & Massimali (tutti gli esercizi)",
      "🏋️ Valutazione Forza & 1RM (Google Sheet)",
      "📊 Tonnellaggio & Volume Pesi",
  ]
  if admin_mode:
    all_tabs = st.tabs(["✍️ Inserisci Carichi"] + tab_labels)
    tab_edit, rest_tabs = all_tabs[0], all_tabs[1:]
  else:
    tab_edit, rest_tabs = None, st.tabs(tab_labels)
  tab_schede, tab_log, tab_force_eval, tab1 = rest_tabs

  with tab_schede:
    st.markdown("##### 📋 Schede Settimanali (lette dai tuoi Google Fogli)")
    sources = load_schede_index()
    if not sources:
      st.info(
          "ℹ️ Nessuna cartella o file collegato. Nel Google Sheet principale"
          " crea una scheda chiamata **Settimane** e scrivi nella colonna A il"
          " link della cartella Drive che contiene i tuoi file (anche con"
          " sottocartelle per settimana), oppure, uno per riga, i link dei file."
          " La cartella e i file devono essere condivisi come «Chiunque abbia il"
          " link → Visualizzatore»."
      )
    else:
      file_ids, folder_notes = list_schede_files(sources)
      df_sch, info_sch = load_schede_settimanali(file_ids)
      if allowed_athletes != "ALL" and not df_sch.empty:
        df_sch = df_sch[df_sch["ATHLETE"].isin(allowed_athletes)]

      with st.expander("🔎 File e schede lette", expanded=df_sch.empty):
        st.caption(f"{len(file_ids)} file da leggere.")
        for note in folder_notes:
          st.caption(note)
        if not info_sch.empty:
          n_bad = int((info_sch["Esito"] != "ok").sum())
          st.caption(
              f"{info_sch['File'].nunique()} file, {len(info_sch)} schede:"
              f" {len(info_sch) - n_bad} lette, {n_bad} con avvisi."
          )
          st.dataframe(
              info_sch.sort_values("Esito", key=lambda s: s.eq("ok")),
              use_container_width=True,
              hide_index=True,
          )
        if st.button("🔄 Ricarica le schede ora", key="sch_reload"):
          _schede_file_cache().clear()
          load_schede_settimanali.clear()
          list_schede_files.clear()
          load_schede_index.clear()
          st.rerun()

      if df_sch.empty:
        st.warning(
            "Non riesco a leggere nessuna serie con carico dalle schede."
            " Nell'elenco qui sopra trovi il motivo."
        )
      else:
        atleti_sch = sorted(df_sch["ATHLETE"].unique())
        settimane_sch = sorted(df_sch["SETTIMANA"].unique(), reverse=True)
        sessioni_sch = sorted(df_sch["SESSIONE"].unique())
        fase_by_week = (
            df_sch[df_sch["FASE"] != ""]
            .groupby("SETTIMANA")["FASE"]
            .agg(lambda s: s.value_counts().index[0])
            .to_dict()
        )

        def _wlabel(w):
          fase = fase_by_week.get(w)
          return f"Week {int(w)}" + (f" — {fase}" if fase else "")

        cs1, cs2, cs3 = st.columns(3)
        with cs1:
          sel_a = st.selectbox("Atleta", atleti_sch, key="sch_atleta")
        with cs2:
          sel_w = st.selectbox(
              "Settimana", settimane_sch, format_func=_wlabel, key="sch_settimana"
          )
        with cs3:
          opts_s = ["Tutte le sedute"] + sessioni_sch
          sel_s = st.selectbox(
              "Seduta",
              opts_s,
              index=opts_s.index("A") if "A" in opts_s else 0,
              format_func=lambda s: SESSIONI_LABEL.get(s, s),
              key="sch_seduta",
          )
        df_a = df_sch[df_sch["ATHLETE"] == sel_a]
        if sel_s != "Tutte le sedute":
          df_a = df_a[df_a["SESSIONE"] == sel_s]
        st.caption(
            "Il 1RM stimato (formula di Epley) è calcolato solo per Back Squat,"
            " Front Squat e Stacco quadrabar. Per tutti gli altri esercizi vedi il"
            " carico massimo e le ripetizioni fatte con quel carico. Per i manubri"
            " il peso è quello di un solo manubrio."
        )

        # --- Scheda della settimana ------------------------------------------
        st.markdown(f"###### 🗓️ Scheda di {sel_a} — {_wlabel(sel_w)}")
        dw = df_a[df_a["SETTIMANA"] == sel_w]
        if dw.empty:
          st.info("Nessun carico per questa settimana e questa seduta.")
        else:
          rows_w = []
          for (sess, _sed, es), g in dw.groupby(
              ["SESSIONE", "SEDUTA", "ESERCIZIO"], sort=False
          ):
            top = g.sort_values(["PESO", "REPS"]).iloc[-1]
            e1 = g["E1RM"].max()
            rows_w.append({
                "Seduta": SESSIONI_LABEL.get(sess, sess),
                "Esercizio": es,
                "Carico massimo": _fmt_set(top["PESO"], top["REPS"]),
                "1RM stimato (Epley)": f"{_fmt_kg(round(e1, 1))} kg" if pd.notna(e1) else "—",
                "Tutte le serie (rip × kg)": "  |  ".join(
                    f"{int(r)}×{_fmt_kg(w)}" for r, w in zip(g["REPS"], g["PESO"])
                ),
                "Note": g["NOTE"].iloc[0],
            })
          st.dataframe(
              pd.DataFrame(rows_w), use_container_width=True, hide_index=True
          )

        # --- Massimali per esercizio -----------------------------------------
        st.markdown(f"###### 🏆 Massimali di {sel_a} (tutte le settimane)")
        rows_m = []
        for es, g in df_a.groupby("ESERCIZIO"):
          top = g.sort_values(["PESO", "REPS"]).iloc[-1]
          last_w = int(g["SETTIMANA"].max())
          g_last = g[g["SETTIMANA"] == last_w]
          top_last = g_last.sort_values(["PESO", "REPS"]).iloc[-1]
          row = {
              "Esercizio": es,
              "Carico massimo": _fmt_set(top["PESO"], top["REPS"]),
              "Settimana del massimo": int(top["SETTIMANA"]),
              "Ultima settimana": last_w,
              "Carico massimo ultima settimana": _fmt_set(
                  top_last["PESO"], top_last["REPS"]
              ),
              "1RM stimato max (Epley)": "—",
              "Settimana del 1RM": "—",
          }
          if g["E1RM"].notna().any():
            best = g.loc[g["E1RM"].idxmax()]
            row["1RM stimato max (Epley)"] = f"{_fmt_kg(round(best['E1RM'], 1))} kg"
            row["Settimana del 1RM"] = int(best["SETTIMANA"])
          rows_m.append(row)
        st.dataframe(pd.DataFrame(rows_m), use_container_width=True, hide_index=True)

        # --- Andamento per singolo esercizio ----------------------------------
        st.markdown(f"###### 📈 Andamento di {sel_a} per esercizio")
        esercizi_sch = sorted(df_a["ESERCIZIO"].unique())
        grid = st.columns(2)
        for k, es in enumerate(esercizi_sch):
          g = df_a[df_a["ESERCIZIO"] == es]
          pts = []
          for wk, gw in g.groupby("SETTIMANA"):
            top = gw.sort_values(["PESO", "REPS"]).iloc[-1]
            serie = _fmt_set(top["PESO"], top["REPS"])
            pts.append({"SETTIMANA": int(wk), "Misura": "Carico massimo (kg)",
                        "Valore": float(top["PESO"]), "Serie": serie})
            if gw["E1RM"].notna().any():
              pts.append({"SETTIMANA": int(wk), "Misura": "1RM stimato (kg)",
                          "Valore": float(gw["E1RM"].max()), "Serie": serie})
          pdf = pd.DataFrame(pts)
          chart_es = (
              alt.Chart(pdf)
              .mark_line(point=True)
              .encode(
                  x=alt.X(
                      "SETTIMANA:Q",
                      title="Settimana",
                      axis=alt.Axis(tickMinStep=1, format="d"),
                  ),
                  y=alt.Y("Valore:Q", title="kg", scale=alt.Scale(zero=False)),
                  color=alt.Color(
                      "Misura:N",
                      title=None,
                      scale=alt.Scale(
                          domain=["1RM stimato (kg)", "Carico massimo (kg)"],
                          range=["#2563eb", "#94a3b8"],
                      ),
                      legend=alt.Legend(orient="bottom"),
                  ),
                  tooltip=[
                      alt.Tooltip("SETTIMANA:Q", title="Settimana", format="d"),
                      "Misura",
                      alt.Tooltip("Valore:Q", title="kg", format=".1f"),
                      alt.Tooltip("Serie:N", title="Serie del carico massimo"),
                  ],
              )
              .properties(height=260)
          )
          with grid[k % 2]:
            st.write(f"**{es}**")
            st.altair_chart(chart_es, use_container_width=True)

  if tab_edit is not None:
    with tab_edit:
      st.markdown("##### ✍️ Inserisci una serie")
      st.caption(
          "Questa scheda compare solo a te: chi usa il link normale vede i dati"
          " ma non può modificarli."
      )
      if "edit_flash" in st.session_state:
        st.success(st.session_state.pop("edit_flash"))

      can_save = has_save_backend()
      if not can_save:
        st.warning(
            "Il salvataggio non è ancora configurato (mancano le impostazioni"
            " di salvataggio nei secrets di Streamlit). Puoi comunque provare"
            " i calcoli."
        )

      with st.expander("🔧 Verifica collegamento con il Google Sheet"):
        st.caption(
            "Controlla, senza scrivere nulla, che lo script e il foglio siano"
            " collegati bene."
        )
        if st.button("Esegui verifica", key="edit_check"):
          ok_w, msg_w = check_apps_script()
          (st.success if ok_w else st.error)(f"Scrittura: {msg_w}")
          ok_r, msg_r = check_read_access()
          (st.success if ok_r else st.error)(f"Lettura: {msg_r}")

      NUOVO_ES = "➕ Nuovo esercizio…"
      giocatori_all = sorted(ruoli_dict.keys())
      esercizi_noti = set(ESERCIZI_BASE)
      if not df_log.empty:
        esercizi_noti |= set(df_log["ESERCIZIO"].unique())

      c1, c2 = st.columns(2)
      with c1:
        e_atleta = st.selectbox("Giocatore", giocatori_all, key="edit_atleta")
      with c2:
        e_scelta = st.selectbox(
            "Esercizio", sorted(esercizi_noti) + [NUOVO_ES], key="edit_esercizio"
        )
      if e_scelta == NUOVO_ES:
        e_esercizio = st.text_input("Nome del nuovo esercizio", key="edit_nuovo_es")
        e_esercizio = e_esercizio.strip()
      else:
        e_esercizio = e_scelta

      # Dati già registrati per questo giocatore / esercizio
      if df_log.empty:
        df_atl = df_atl_es = df_log
      else:
        df_atl = df_log[df_log["ATHLETE"] == e_atleta]
        df_atl_es = df_atl[df_atl["ESERCIZIO"] == e_esercizio]

      bw_def = latest_value(df_atl, "BW") or 0.0
      tgt_def = latest_value(df_atl_es, "TARGET")
      if tgt_def is None and not df_log.empty:
        tgt_def = latest_value(df_log[df_log["ESERCIZIO"] == e_esercizio], "TARGET")
      tgt_def = tgt_def or 0.0

      c3, c4, c5, c6 = st.columns(4)
      with c3:
        e_kg = st.number_input(
            "Kg", min_value=0.0, max_value=600.0, value=100.0, step=2.5, key="edit_kg"
        )
      with c4:
        e_reps = st.number_input(
            "Ripetizioni", min_value=1, max_value=30, value=5, step=1, key="edit_reps"
        )
      with c5:
        e_rir_sel = st.selectbox(
            "RIR (facoltativo)", ["—", 0, 1, 2, 3, 4, 5], key="edit_rir"
        )
      with c6:
        e_data = st.date_input("Data", value=date.today(), key="edit_data")

      c7, c8 = st.columns(2)
      with c7:
        e_bw = st.number_input(
            "Peso corporeo (kg)",
            min_value=0.0,
            max_value=250.0,
            value=float(bw_def),
            step=0.5,
            key=f"edit_bw_{e_atleta}",
            help="Serve per la forza relativa. 0 = non indicato.",
        )
      with c8:
        e_target = st.number_input(
            "Target forza relativa (× peso corporeo)",
            min_value=0.0,
            max_value=10.0,
            value=float(tgt_def),
            step=0.05,
            key=f"edit_target_{e_atleta}_{e_esercizio}",
            help="Es. 1.8 = 1RM pari a 1,8 volte il peso corporeo. 0 = nessun target.",
        )
      e_note = st.text_input("Note (facoltativo)", key="edit_note")

      # --- Calcoli in tempo reale -------------------------------------------
      e_rir = None if e_rir_sel == "—" else int(e_rir_sel)
      e1rm_new = epley_1rm(e_kg, e_reps, e_rir or 0)
      reps_eff = e_reps + (e_rir or 0)
      reliable = reps_eff <= 10
      prev_best = df_atl_es["E1RM"].max() if len(df_atl_es) else float("nan")
      cand = [v for v in [None if pd.isna(prev_best) else float(prev_best),
                          e1rm_new if reliable else None] if v is not None]
      forza_max = max(cand) if cand else None

      st.markdown("###### 🧮 Calcolo con questa serie")
      m1, m2, m3, m4 = st.columns(4)
      m1.metric("1RM teorico (Epley)", f"{e1rm_new:.1f} kg")
      m2.metric(
          "Forza massima attuale",
          f"{forza_max:.1f} kg" if forza_max else "—",
      )
      rel = (forza_max / e_bw) if (forza_max and e_bw > 0) else None
      m3.metric("Forza relativa (× BW)", f"{rel:.2f}" if rel else "—")
      if e_target > 0 and e_bw > 0:
        ideale = e_target * e_bw
        perc = (forza_max or 0) / ideale * 100
        m4.metric(
            "Target (1RM ideale)",
            f"{ideale:.1f} kg",
            f"{perc:.0f}% raggiunto",
            delta_color="off",
        )
      else:
        m4.metric("Target (1RM ideale)", "—")
      st.caption(
          f"1RM = {e_kg:g} × (1 + ({e_reps} + {e_rir or 0}) / 30). Con più di 10"
          " ripetizioni (RIR compreso) la stima non è affidabile e la serie non"
          " entra nella forza massima."
      )

      if st.button("💾 Salva serie", disabled=not can_save, key="edit_save"):
        if not e_esercizio:
          st.error("Scrivi il nome dell'esercizio.")
        elif e_kg <= 0:
          st.error("Inserisci i kg sollevati.")
        else:
          try:
            append_log_row({
                "DATA": e_data.strftime("%Y-%m-%d"),
                "ATLETA": e_atleta,
                "ESERCIZIO": e_esercizio,
                "PESO": float(e_kg),
                "REPS": int(e_reps),
                "RIR": e_rir if e_rir is not None else "",
                "BW": float(e_bw) if e_bw > 0 else "",
                "TARGET": float(e_target) if e_target > 0 else "",
                "NOTE": e_note.strip(),
            })
            load_google_sheet_log.clear()
            st.session_state["edit_flash"] = (
                f"✅ Salvato: {e_atleta} — {e_esercizio}, {e_kg:g} kg × {e_reps}"
                f" (1RM stimato {e1rm_new:.1f} kg)"
            )
            st.rerun()
          except Exception as exc:
            st.error(f"Non sono riuscito a salvare ({type(exc).__name__}): {exc}")

      if len(df_atl_es):
        st.markdown("###### 🕘 Ultime serie registrate per questo esercizio")
        recent = df_atl_es.sort_values("DATE_DT", ascending=False, kind="stable")
        recent = recent[["DATE_STR", "SERIE", "RIR", "E1RM", "NOTE"]].head(8).copy()
        recent["E1RM"] = recent["E1RM"].round(1)
        recent.columns = ["Data", "Serie", "RIR", "1RM stimato (kg)", "Note"]
        st.dataframe(recent, use_container_width=True, hide_index=True)

  with tab_log:
    st.markdown("##### 📈 Carichi, Massimali & Andamento per Esercizio")

    if df_log.empty:
      if admin_mode:
        st.info(
            "ℹ️ Nessuna serie registrata (o scheda non leggibile). Inserisci la"
            " prima dalla scheda **✍️ Inserisci Carichi**: la scheda «Carichi»"
            " del Google Sheet viene creata da sola al primo salvataggio."
        )
        st.caption(f"🔎 Diagnosi: {diagnose_log_sheet()}")
      else:
        st.info("ℹ️ Nessun carico registrato per ora.")
    else:
      st.caption(
          "1RM stimato = Peso × (1 + (Reps + RIR) / 30), formula di Epley,"
          " considerato attendibile fino a 10 ripetizioni."
          " Esempio: 120 kg × 4 → circa 136 kg."
      )

      atleti_log = sorted(df_log["ATHLETE"].unique())
      opzioni_atleti = ["Tutti gli atleti"] + atleti_log
      col_s1, col_s2 = st.columns(2)
      with col_s1:
        sel_atleta = st.selectbox(
            "Atleta",
            opzioni_atleti,
            index=1 if len(atleti_log) == 1 else 0,
            key="log_atleta",
        )
      df_l = (
          df_log
          if sel_atleta == "Tutti gli atleti"
          else df_log[df_log["ATHLETE"] == sel_atleta]
      )
      esercizi_log = sorted(df_l["ESERCIZIO"].unique())
      with col_s2:
        sel_es = st.selectbox("Esercizio", esercizi_log, key="log_esercizio")

      # --- Massimali per esercizio -------------------------------------------
      rows = []
      for (atl, es), g in df_l.groupby(["ATHLETE", "ESERCIZIO"]):
        g_e = g.dropna(subset=["E1RM"])
        best_e = g_e.loc[g_e["E1RM"].idxmax()] if not g_e.empty else None
        best_w = g.loc[g["PESO"].idxmax()]
        last = g.sort_values("DATE_DT", kind="stable").iloc[-1]

        # Peso corporeo attuale e target di forza relativa (ultimi inseriti)
        bw_now = latest_value(df_log[df_log["ATHLETE"] == atl], "BW")
        tgt = latest_value(g, "TARGET")
        if tgt is None:
          tgt = latest_value(df_log[df_log["ESERCIZIO"] == es], "TARGET")
        e1 = float(best_e["E1RM"]) if best_e is not None else None
        ideale = tgt * bw_now if (tgt and bw_now) else None

        rows.append({
            "ATLETA": atl,
            "ESERCIZIO": es,
            "E1RM": round(e1, 1) if e1 is not None else None,
            "SERIE_E1RM": best_e["SERIE"] if best_e is not None else "",
            "DATA_E1RM": best_e["DATE_STR"] if best_e is not None else "",
            "BW": bw_now,
            "FORZA_REL": round(e1 / bw_now, 2) if (e1 and bw_now) else None,
            "TARGET": tgt,
            "IDEALE": round(ideale, 1) if ideale else None,
            "PERC_TARGET": round(e1 / ideale * 100) if (e1 and ideale) else None,
            "PESO_MAX": float(best_w["PESO"]),
            "SERIE_PESO_MAX": best_w["SERIE"],
            "ULTIMA_DATA": last["DATE_STR"],
            "ULTIMA_SERIE": last["SERIE"],
            "N_SERIE": int(len(g)),
            "TONNAGE": float(round(g["TONNAGE"].sum())),
        })
      summ = pd.DataFrame(rows)

      st.markdown("###### 🏆 Massimali per esercizio")
      st.dataframe(
          summ.sort_values(["ATLETA", "ESERCIZIO"]).rename(
              columns={
                  "ATLETA": "Atleta",
                  "ESERCIZIO": "Esercizio",
                  "E1RM": "Forza massima attuale: 1RM stimato (kg)",
                  "SERIE_E1RM": "Serie del 1RM",
                  "DATA_E1RM": "Data 1RM",
                  "BW": "Peso corporeo (kg)",
                  "FORZA_REL": "Forza relativa (×BW)",
                  "TARGET": "Target (×BW)",
                  "IDEALE": "1RM ideale (kg)",
                  "PERC_TARGET": "% del target",
                  "PESO_MAX": "Carico max (kg)",
                  "SERIE_PESO_MAX": "Serie del carico max",
                  "ULTIMA_DATA": "Ultima seduta",
                  "ULTIMA_SERIE": "Ultima serie",
                  "N_SERIE": "Serie totali",
                  "TONNAGE": "Tonnellaggio (kg)",
              }
          ),
          use_container_width=True,
          hide_index=True,
      )

      # Sintesi per l'atleta e l'esercizio scelti
      if sel_atleta != "Tutti gli atleti":
        sel_row = summ[summ["ESERCIZIO"] == sel_es]
        if not sel_row.empty:
          r0 = sel_row.iloc[0]
          k1, k2, k3, k4 = st.columns(4)
          k1.metric(
              "Forza massima attuale (1RM)",
              f"{r0['E1RM']:.1f} kg" if pd.notna(r0["E1RM"]) else "—",
          )
          k2.metric(
              "Forza relativa (× BW)",
              f"{r0['FORZA_REL']:.2f}" if pd.notna(r0["FORZA_REL"]) else "—",
          )
          k3.metric(
              "Target forza relativa",
              f"{r0['TARGET']:.2f} × BW" if pd.notna(r0["TARGET"]) else "—",
          )
          k4.metric(
              "Target raggiunto",
              f"{r0['PERC_TARGET']:.0f}%" if pd.notna(r0["PERC_TARGET"]) else "—",
          )

      if sel_atleta == "Tutti gli atleti":
        bar_df = summ[summ["ESERCIZIO"] == sel_es].dropna(subset=["E1RM"])
        bar_x, bar_title = "ATLETA", f"1RM stimato (kg) — {sel_es}"
      else:
        bar_df = summ.dropna(subset=["E1RM"])
        bar_x, bar_title = "ESERCIZIO", f"1RM stimato (kg) — {sel_atleta}"
      if not bar_df.empty:
        st.write(f"**{bar_title}**")
        bar_order = bar_df.sort_values("E1RM", ascending=False)[bar_x].tolist()
        bars_log = (
            alt.Chart(bar_df)
            .mark_bar(color="#2563eb")
            .encode(
                x=alt.X(f"{bar_x}:N", sort=bar_order, title=None),
                y=alt.Y("E1RM:Q", title="1RM stimato (kg)"),
                tooltip=[
                    "ATLETA",
                    "ESERCIZIO",
                    alt.Tooltip("E1RM:Q", title="1RM stimato (kg)", format=".1f"),
                    alt.Tooltip("SERIE_E1RM:N", title="Serie"),
                    alt.Tooltip("DATA_E1RM:N", title="Data"),
                    alt.Tooltip("FORZA_REL:Q", title="Forza relativa (×BW)", format=".2f"),
                    alt.Tooltip("PERC_TARGET:Q", title="% del target", format=".0f"),
                ],
            )
        )
        ideal_df = bar_df.dropna(subset=["IDEALE"])
        if ideal_df.empty:
          chart_bar = bars_log.properties(height=340)
        else:
          ticks = (
              alt.Chart(ideal_df)
              .mark_tick(color="#f97316", thickness=4, size=60)
              .encode(
                  x=alt.X(f"{bar_x}:N", sort=bar_order),
                  y=alt.Y("IDEALE:Q"),
                  tooltip=[
                      "ATLETA",
                      "ESERCIZIO",
                      alt.Tooltip("IDEALE:Q", title="1RM ideale (kg)", format=".1f"),
                      alt.Tooltip("TARGET:Q", title="Target (×BW)", format=".2f"),
                  ],
              )
          )
          chart_bar = alt.layer(bars_log, ticks).properties(height=340)
        st.altair_chart(chart_bar, use_container_width=True)
        if not ideal_df.empty:
          st.caption(
              "🟠 Tacca arancione = 1RM ideale (target forza relativa × peso"
              " corporeo)"
          )

      # --- Andamento nel tempo per esercizio ----------------------------------
      st.markdown(f"###### 📈 Andamento — {sel_es}")
      metriche = {
          "1RM stimato (kg)": "E1RM",
          "Carico massimo (kg)": "PESO_MAX",
          "Tonnellaggio (kg)": "TONNAGE",
      }
      sel_metrica = st.radio(
          "Mostra", list(metriche.keys()), horizontal=True, key="log_metrica"
      )
      metric_col = metriche[sel_metrica]

      df_t = df_l[df_l["ESERCIZIO"] == sel_es]
      daily_log = (
          df_t.groupby(["ATHLETE", "DATE_STR"])
          .agg(
              E1RM=("E1RM", "max"),
              PESO_MAX=("PESO", "max"),
              TONNAGE=("TONNAGE", "sum"),
          )
          .reset_index()
      )
      top_idx = df_t.groupby(["ATHLETE", "DATE_STR"])["PESO"].idxmax()
      top_sets = df_t.loc[top_idx, ["ATHLETE", "DATE_STR", "SERIE"]].rename(
          columns={"SERIE": "SERIE_TOP"}
      )
      daily_log = daily_log.merge(top_sets, on=["ATHLETE", "DATE_STR"], how="left")
      daily_log["DATA"] = pd.to_datetime(daily_log["DATE_STR"])
      plot_log = daily_log.dropna(subset=[metric_col])

      if plot_log.empty:
        st.info("Nessun dato disponibile per questa misura.")
      else:
        chart_tr = (
            alt.Chart(plot_log)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    "DATA:T",
                    title="Data seduta",
                    axis=alt.Axis(format="%d/%m"),
                ),
                y=alt.Y(
                    f"{metric_col}:Q",
                    title=sel_metrica,
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color("ATHLETE:N", title="Atleta"),
                tooltip=[
                    "ATHLETE",
                    alt.Tooltip("DATE_STR:N", title="Data"),
                    alt.Tooltip("SERIE_TOP:N", title="Serie col carico maggiore"),
                    alt.Tooltip("E1RM:Q", title="1RM stimato (kg)", format=".1f"),
                    alt.Tooltip("PESO_MAX:Q", title="Carico max (kg)"),
                    alt.Tooltip("TONNAGE:Q", title="Tonnellaggio (kg)", format=".0f"),
                ],
            )
            .properties(height=380)
        )
        st.altair_chart(chart_tr, use_container_width=True)

      # --- Tutte le serie registrate (più recenti per prime) -------------------
      with st.expander("📋 Tutte le serie registrate", expanded=False):
        log_view = df_l.sort_values(
            "DATE_DT", ascending=False, kind="stable"
        )[
            [
                "DATE_STR",
                "ATHLETE",
                "ESERCIZIO",
                "PESO",
                "REPS",
                "RIR",
                "E1RM",
                "TONNAGE",
                "NOTE",
            ]
        ].copy()
        log_view["E1RM"] = log_view["E1RM"].round(1)
        log_view.columns = [
            "Data",
            "Atleta",
            "Esercizio",
            "Peso (kg)",
            "Reps",
            "RIR",
            "1RM stimato (kg)",
            "Tonnellaggio (kg)",
            "Note",
        ]
        st.dataframe(log_view, use_container_width=True, hide_index=True)

  with tab_force_eval:
    st.markdown(
        "##### 🏋️‍♂️ Valutazione Forza & Massimali Teorici (Sincronizzato da"
        " Google Drive)"
    )

    if not df_force.empty and "ESERCIZIO" in df_force.columns:
      col_ex1, col_ex2 = st.columns([1, 2])
      with col_ex1:
        selected_ex = st.selectbox(
            "Seleziona Esercizio di Forza:", df_force["ESERCIZIO"].unique()
        )

      df_force_sub = df_force[df_force["ESERCIZIO"] == selected_ex]

      giocatori_force = sorted(df_force_sub["ATHLETE"].unique())
      selected_f_players = st.multiselect(
          "Filtra per Giocatore/i:", giocatori_force, default=giocatori_force
      )

      if selected_f_players:
        df_force_sub = df_force_sub[
            df_force_sub["ATHLETE"].isin(selected_f_players)
        ]

      cols_to_show = [
          c
          for c in [
              "ATHLETE",
              "ROLE",
              "BW",
              "Peso usato",
              "Reps",
              "RIR",
              "1RM Teorico",
              "1RM/BW",
              "1RM Ideale",
          ]
          if c in df_force_sub.columns
      ]

      st.dataframe(df_force_sub[cols_to_show], use_container_width=True)

      col_f1, col_f2 = st.columns(2)
      with col_f1:
        st.write(f"**1RM Teorico (kg) — {selected_ex}**")
        chart_1rm = (
            alt.Chart(df_force_sub)
            .mark_bar(color="#2563eb")
            .encode(
                x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                y=alt.Y("1RM Teorico:Q", title="1RM Teorico (kg)"),
                tooltip=[
                    c
                    for c in [
                        "ATHLETE",
                        "BW",
                        "Peso usato",
                        "Reps",
                        "1RM Teorico",
                        "1RM/BW",
                    ]
                    if c in df_force_sub.columns
                ],
            )
            .properties(height=360)
        )
        st.altair_chart(chart_1rm, use_container_width=True)

      with col_f2:
        st.write(f"**Forza Relativa (1RM / BW) — {selected_ex}**")
        chart_fr = (
            alt.Chart(df_force_sub)
            .mark_bar(color="#16a34a")
            .encode(
                x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                y=alt.Y("1RM/BW:Q", title="Forza Relativa (xBW)"),
                tooltip=[
                    c
                    for c in ["ATHLETE", "BW", "1RM/BW", "1RM Teorico"]
                    if c in df_force_sub.columns
                ],
            )
            .properties(height=360)
        )
        st.altair_chart(chart_fr, use_container_width=True)
    else:
      st.info(
          "ℹ️ Impossibile caricare il foglio Google di valutazione della forza."
      )

  with tab1:
    if not df_load.empty:
      load_daily = (
          df_load.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"])
          .agg(TONNELLAGGIO_GIORNO=("TOTAL_LOAD", "sum"))
          .reset_index()
      )
      st.markdown("##### 🏋️‍♂️ Tonnellaggio Sollevato per Data e Giocatore (kg)")
      chart_l1 = (
          alt.Chart(load_daily)
          .mark_bar()
          .encode(
              x=alt.X("DATE_STR:N", title="Data Seduta Pesi"),
              y=alt.Y("TONNELLAGGIO_GIORNO:Q", title="Tonnellaggio Totale (kg)"),
              color=alt.Color("ATHLETE:N", title="Giocatore"),
              tooltip=["DATE_STR", "ATHLETE", "TONNELLAGGIO_GIORNO"],
          )
          .properties(height=380)
      )
      st.altair_chart(chart_l1, use_container_width=True)
    else:
      st.info("ℹ️ Nessun dato di tonnellaggio disponibile.")
