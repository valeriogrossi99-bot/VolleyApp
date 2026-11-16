"""pliche.py — sezione Pliche Cutanee (plicometria / composizione corporea).

I dati vengono letti dal Google Sheet delle pliche (prima scheda del foglio).
Per modificare i dati si lavora direttamente sul Google Sheet.
"""
import io

import pandas as pd
import requests

from core import *

PLICHE_SHEET_ID = "1zH8w4hePJK531fxq0RGGX7az76EEz4c7vXWF5tCM1mc"
PLICHE_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{PLICHE_SHEET_ID}/edit?usp=sharing"
)
PLICHE_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{PLICHE_SHEET_ID}/export?format=csv"
)

# Nomi possibili della colonna con il nome dell'atleta
PLICHE_ATHLETE_COLUMNS = {"ATLETA", "ATHLETE", "GIOCATORE", "PLAYER", "NOME", "COGNOME"}

EN_STATIC.update({
    "Plicometria & Composizione Corporea": "Skinfolds & Body Composition",
    "### 📏 **Pliche Cutanee** — Plicometria & Composizione Corporea": (
        "### 📏 **Skinfolds** — Skinfold Measurements & Body Composition"
    ),
    "📂 Apri il Google Sheet delle pliche": "📂 Open the skinfolds Google Sheet",
    "ℹ️ Impossibile leggere il foglio delle pliche: controlla che sia condiviso con"
    " «chiunque abbia il link».": (
        "ℹ️ Unable to read the skinfolds sheet: check that it is shared with"
        " “anyone with the link”."
    ),
    "ℹ️ Il foglio delle pliche è vuoto.": "ℹ️ The skinfolds sheet is empty.",
    "ℹ️ In questa vista non è possibile mostrare le pliche: non trovo la colonna"
    " con il nome dell'atleta.": (
        "ℹ️ Skinfolds can't be shown in this view: the athlete name column was"
        " not found."
    ),
    "Pliche Cutanee": "Skinfolds",
    "Filtra per Giocatore": "Filter by Player",
})


@st.cache_data(ttl=300)
def load_pliche_sheet():
  """Legge la prima scheda del Google Sheet delle pliche come tabella."""
  try:
    r = requests.get(PLICHE_CSV_URL, headers=REQ_HEADERS, timeout=15)
    if r.status_code != 200:
      return pd.DataFrame()
    df = pd.read_csv(io.StringIO(r.content.decode("utf-8")), dtype=str)
  except Exception:
    return pd.DataFrame()
  df = df.dropna(how="all").dropna(axis=1, how="all").fillna("")
  return df


def _athlete_column(df):
  for c in df.columns:
    if str(c).strip().upper() in PLICHE_ATHLETE_COLUMNS:
      return c
  return None


def _matches(value, athlete):
  """True se il testo della cella si riferisce all'atleta indicato."""
  keys = {athlete.split()[-1], athlete}
  keys |= {k for k, full in cognomi_to_full.items() if full == athlete}
  v = _slug(value)
  return any(_slug(k) and _slug(k) in v for k in keys)


def render(allowed_athletes):
  """Disegna la pagina Pliche Cutanee."""
  col_h1, col_h2 = st.columns([8, 2])
  with col_h1:
    st.markdown("### 📏 **Pliche Cutanee** — Plicometria & Composizione Corporea")
  with col_h2:
    if st.button("🏠 Torna alla Home", use_container_width=True):
      st.session_state.page = "home"
      st.rerun()

  if allowed_athletes == "ALL":
    st.sidebar.success("🔓 Visualizzazione: Roster Completo")
  else:
    st.sidebar.success(f"🔓 Visualizzazione Dedicata: {allowed_athletes[0]}")

  # Il link al foglio completo (con i dati di tutti) solo nella vista completa
  if allowed_athletes == "ALL":
    st.link_button(T("📂 Apri il Google Sheet delle pliche"), PLICHE_SHEET_URL)

  df_pliche = load_pliche_sheet()
  if df_pliche.empty:
    st.info(
        "ℹ️ Impossibile leggere il foglio delle pliche: controlla che sia"
        " condiviso con «chiunque abbia il link»."
    )
    return

  col_ath = _athlete_column(df_pliche)

  if allowed_athletes != "ALL":
    # Vista dedicata a un solo atleta: mostro solo le sue righe
    if col_ath is None:
      st.info(
          "ℹ️ In questa vista non è possibile mostrare le pliche: non trovo la"
          " colonna con il nome dell'atleta."
      )
      return
    df_pliche = df_pliche[
        df_pliche[col_ath].map(lambda v: _matches(v, allowed_athletes[0]))
    ]
  elif col_ath is not None:
    st.sidebar.divider()
    st.sidebar.header("🔍 Filtri Selezione & Confronto")
    names = sorted(x for x in df_pliche[col_ath].unique() if str(x).strip())
    selected = st.sidebar.multiselect("Filtra per Giocatore", names)
    if selected:
      df_pliche = df_pliche[df_pliche[col_ath].isin(selected)]

  st.dataframe(df_pliche, use_container_width=True, hide_index=True)

