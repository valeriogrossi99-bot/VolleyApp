"""pliche.py — sezione Pliche Cutanee (plicometria).

Il Google Sheet "Antropometria Cuneo" ha una scheda per ogni data (nome della
scheda in formato gg/mm, ad es. "24/08", oppure "20-22/10" se la misurazione è
su più giorni). Per ogni scheda l'app cerca il nome di ogni giocatore, riconosce
dove sono i suoi dati e legge le 6 pliche (tricipite, sottoscapolare, obliquo,
addominale, quadricipite, polpaccio) e il peso. Per ogni giocatore selezionato
mostra una tabella (peso, 6 pliche, media delle pliche) con solo le date in cui
ha dei dati, e due grafici: andamento del peso e andamento della media pliche.

Per aggiungere una nuova misurazione basta aggiungere una scheda con la data
nel Google Sheet (l'app si aggiorna da sola entro un paio di minuti).
"""
import io
import re

import altair as alt
import pandas as pd
import requests

from core import *

PLICHE_SHEET_ID = "1zH8w4hePJK531fxq0RGGX7az76EEz4c7vXWF5tCM1mc"
PLICHE_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{PLICHE_SHEET_ID}/edit?usp=sharing"
)
PLICHE_XLSX_URL = (
    f"https://docs.google.com/spreadsheets/d/{PLICHE_SHEET_ID}/export?format=xlsx"
)

# (nome mostrato, inizio del nome nel foglio in minuscolo e senza spazi/accenti)
PLICHE_KEYS = [
    ("Tricipite", "tricipite"),
    ("Sottoscapolare", "sottoscapolare"),
    ("Obliquo", "obliquo"),
    ("Addominale", "addominale"),
    ("Quadricipite", "quadricipite"),
    ("Polpaccio", "polpaccio"),
]
PESO_KEY = ("Peso", "peso")
PLICHE_NAMES = [n for n, _ in PLICHE_KEYS]
KEY_TO_NAME = {k: n for n, k in PLICHE_KEYS + [PESO_KEY]}
PESO_LABEL = "Peso (kg)"
MEDIA_LABEL = "Media pliche (mm)"
PESO_COLOR = "#2563eb"
MEDIA_COLOR = "#db2777"

# Nome scheda = data: "24/08", "13/11", "20-22/10", "27-29/10"
TAB_DATE_RX = re.compile(r"^\s*(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?\s*/\s*(\d{1,2})\s*$")
NUM_RX = re.compile(r"^\s*(-?\d+(?:[.,]\d+)?)\s*(?:mm)?\s*$", re.I)
# Se il giocatore ha più misure vicine (2-3 rilevazioni), le leggo e ne faccio la media
MAX_COLS_PER_PLAYER = 6

_NEW_EN = {
    "### 📏 **Pliche Cutanee** — Peso, pliche e andamento": (
        "### 📏 **Skinfolds** — Weight, skinfolds and trend"
    ),
    "Plicometria & Composizione Corporea": "Skinfolds & Body Composition",
    "📂 Apri il Google Sheet delle pliche": "📂 Open the skinfolds Google Sheet",
    "ℹ️ Nel foglio non ho trovato dati di pliche leggibili.": (
        "ℹ️ No readable skinfold data found in the sheet."
    ),
    "ℹ️ Nessun dato di pliche per questo giocatore.": (
        "ℹ️ No skinfold data for this player."
    ),
    "ℹ️ Seleziona almeno un giocatore.": "ℹ️ Select at least one player.",
    "Seleziona i giocatori": "Select players",
    "Pliche Cutanee": "Skinfolds",
    "Peso (kg)": "Weight (kg)",
    "Media pliche (mm)": "Skinfold average (mm)",
    "Data": "Date",
    "Tricipite": "Triceps",
    "Sottoscapolare": "Subscapular",
    "Obliquo": "Oblique",
    "Addominale": "Abdominal",
    "Quadricipite": "Quadriceps",
    "Polpaccio": "Calf",
    "**⚖️ Andamento del peso**": "**⚖️ Weight trend**",
    "**📉 Andamento della media delle pliche**": "**📉 Skinfold average trend**",
    "Nessun dato di peso per questo giocatore.": "No weight data for this player.",
    "Nessun dato di pliche per questo giocatore.": "No skinfold data for this player.",
    "La media è calcolata sulle pliche rilevate in ogni data. Sono mostrate solo le date con dati.": (
        "The average is calculated on the skinfolds measured on each date. Only dates with data are shown."
    ),
    "🔧 Diagnostica lettura del foglio": "🔧 Sheet reading diagnostics",
    "Scheda da controllare": "Sheet to check",
}
for _k, _v in _NEW_EN.items():
  EN_STATIC.setdefault(_k, _v)


# ------------------------------------------------------------------------------
# Lettura del foglio: una scheda = una data
# ------------------------------------------------------------------------------
def _tab_date(name):
  """'24/08' -> data ordinabile (stagione 2026/27); None se non è una data."""
  m = TAB_DATE_RX.match(str(name))
  if not m:
    return None
  day, month = int(m.group(1)), int(m.group(3))
  year = ANCHOR_MONDAY.year if month >= 7 else ANCHOR_MONDAY.year + 1
  try:
    return pd.Timestamp(year=year, month=month, day=day)
  except Exception:
    return None


def _num(text, vmax=100):
  m = NUM_RX.match(str(text))
  if not m:
    return None
  try:
    v = float(m.group(1).replace(",", "."))
  except ValueError:
    return None
  return v if 0 < v <= vmax else None


def _player_keys():
  """Per ogni giocatore le forme del nome che riconosco nelle celle."""
  out = {}
  for full in ruoli_dict:
    parts = full.split()
    first, last = _slug(parts[0]), _slug(parts[-1])
    keys = {_slug(full), last + first, last}
    keys |= {_slug(k) for k, f in cognomi_to_full.items() if f == full}
    out[full] = ({k for k in keys if k}, len(first))
  return out


def _match_player(text, pkeys):
  if len(text) > 40:
    return None
  s = _slug(text)
  if not s:
    return None
  for full, (keys, flen) in pkeys.items():
    for k in keys:
      if s == k or (s.startswith(k) and len(s) <= len(k) + flen + 2):
        return full
  return None


def _labels(g):
  """Celle con il nome delle pliche e celle-titolo 'PLICHE'."""
  labs = {key: [] for _, key in PLICHE_KEYS + [PESO_KEY]}
  heads = []
  for r in range(g.shape[0]):
    for c in range(g.shape[1]):
      t = g[r, c].strip()
      if not t:
        continue
      s = _slug(t)
      if not s:
        continue
      if len(t) <= 20 and s.startswith("pliche"):
        heads.append((r, c))
        continue
      if len(t) <= 200:
        for _, key in PLICHE_KEYS + [PESO_KEY]:
          if s.startswith(key):
            labs[key].append((r, c))
            break
  return labs, heads


def _orientation(labs):
  """'V' = nomi delle pliche in colonna (giocatori affiancati); 'H' = in riga."""
  pos = [max(labs[k]) for _, k in PLICHE_KEYS if labs[k]]
  if len(pos) < 2:
    return "V"
  rows = {p[0] for p in pos}
  cols = {p[1] for p in pos}
  return "V" if len(rows) >= len(cols) else "H"


def _parse_tab(g, pkeys):
  """Legge una scheda: {(giocatore, plica): (distanza, valore medio, n)}."""
  labs, heads = _labels(g)
  orient = "V"
  if any(labs[k] for _, k in PLICHE_KEYS):
    orient = _orientation(labs)
    if orient == "H":
      g = g.T
      labs, heads = _labels(g)

  anchors = []
  for r in range(g.shape[0]):
    for c in range(g.shape[1]):
      t = g[r, c].strip()
      if t:
        p = _match_player(t, pkeys)
        if p:
          anchors.append((p, r, c))

  found = {}
  for p, ar, ac in anchors:
    # titolo "PLICHE" più vicino sotto il nome del giocatore
    hdr = min((h[0] for h in heads if h[0] > ar), default=None)
    # il blocco del giocatore finisce dove ne comincia un altro nella stessa colonna
    below = [a[1] for a in anchors if a[2] == ac and a[1] > ar]
    limit = min(below) if below else 10**9
    # colonne dei suoi dati: fino al giocatore successivo sulla stessa riga
    right = [a[2] for a in anchors if a[1] == ar and a[2] > ac]
    cend = min(right) if right else ac + MAX_COLS_PER_PLAYER
    cend = min(cend, ac + MAX_COLS_PER_PLAYER, g.shape[1])
    for _, key in PLICHE_KEYS + [PESO_KEY]:
      is_w = key == PESO_KEY[1]
      if is_w:
        # il peso è la riga col nome "Peso" più vicina sotto il giocatore
        cands = [q for q in labs[key] if ar < q[0] < limit]
      else:
        cands = [
            q for q in labs[key]
            if ar < q[0] < limit and (hdr is None or q[0] > hdr)
        ]
      if not cands:
        continue
      lr, lc = min(cands) if (is_w or hdr is not None) else max(cands)
      vals = [_num(g[lr, c], 250 if is_w else 100)
              for c in range(ac, cend) if c != lc]
      vals = [v for v in vals if v is not None]
      if not vals:
        continue
      dist = lr - ar
      cur = found.get((p, key))
      if cur is None or dist < cur[0]:
        found[(p, key)] = (dist, sum(vals) / len(vals), len(vals))
  return found, anchors, orient


@st.cache_data(ttl=120, show_spinner=False)
def load_pliche_data():
  """Scarica il foglio e restituisce (pliche, diagnostica, anteprima, errore)."""
  empty = pd.DataFrame()
  try:
    r = requests.get(PLICHE_XLSX_URL, headers=REQ_HEADERS, timeout=60)
    if r.status_code != 200 or r.content[:2] != b"PK":
      return empty, empty, {}, (
          f"codice {r.status_code}: il foglio deve essere condiviso con"
          " «chiunque abbia il link» (Visualizzatore)"
      )
    book = pd.read_excel(io.BytesIO(r.content), sheet_name=None, header=None)
  except ImportError:
    return empty, empty, {}, "manca la libreria openpyxl (aggiungila al requirements.txt)"
  except Exception as e:
    return empty, empty, {}, f"{type(e).__name__}: {e}"

  pkeys = _player_keys()
  rows, diag, raw = [], [], {}
  for name, df in book.items():
    name = str(name).strip()
    raw[name] = df.iloc[:60, :30].fillna("").astype(str)
    d = _tab_date(name)
    if d is None:
      diag.append({"Scheda": name, "Stato": "ignorata (il nome non è una data gg/mm)",
                   "Disposizione": "", "Giocatori trovati": 0, "Valori letti": 0,
                   "Peso letto": 0})
      continue
    g = df.fillna("").astype(str).to_numpy()
    found, anchors, orient = _parse_tab(g, pkeys)
    for (p, key), (_, val, n) in found.items():
      rows.append({
          "ATHLETE": p, "SCHEDA": name, "DATA": d,
          "PLICA": KEY_TO_NAME[key], "VALORE": val, "N": n,
      })
    diag.append({
        "Scheda": name, "Stato": "letta",
        "Disposizione": "pliche in colonna" if orient == "V" else "pliche in riga",
        "Giocatori trovati": len({a[0] for a in anchors}),
        "Valori letti": len(found),
        "Peso letto": sum(1 for (_, k) in found if k == PESO_KEY[1]),
    })
  df_long = pd.DataFrame(rows)
  return df_long, pd.DataFrame(diag), raw, None


# ------------------------------------------------------------------------------
# Grafici
# ------------------------------------------------------------------------------
def _trend_chart(wide, col, title, color):
  """Andamento di una colonna (peso o media pliche) solo sulle date con dato."""
  d = wide[["SCHEDA", col]].dropna().rename(columns={col: "VALORE"})
  base = alt.Chart(d).encode(
      x=alt.X("SCHEDA:N", title="Data", sort=d["SCHEDA"].tolist(),
              axis=alt.Axis(labelAngle=0)),
      y=alt.Y("VALORE:Q", title=title, scale=alt.Scale(zero=False)),
  )
  line = base.mark_line(point=alt.OverlayMarkDef(size=90), color=color).encode(
      tooltip=[
          alt.Tooltip("SCHEDA:N", title="Data"),
          alt.Tooltip("VALORE:Q", title=title, format=".1f"),
      ]
  )
  labels = base.mark_text(dy=-14, color=color).encode(
      text=alt.Text("VALORE:Q", format=".1f")
  )
  return alt.layer(line, labels).properties(height=280)


# ------------------------------------------------------------------------------
# Pagina
# ------------------------------------------------------------------------------
SURNAME = {full: k for k, full in cognomi_to_full.items()}


def _label(p):
  return SURNAME.get(p, p.split()[-1])


def _player_table(d):
  """Una riga per data (solo date con dati): peso, 6 pliche, media pliche."""
  wide = d.pivot_table(
      index=["DATA", "SCHEDA"], columns="PLICA", values="VALORE", aggfunc="mean"
  ).reset_index().sort_values("DATA")
  wide.columns.name = None
  for n in PLICHE_NAMES + [PESO_KEY[0]]:
    if n not in wide.columns:
      wide[n] = float("nan")
  wide[MEDIA_LABEL] = wide[PLICHE_NAMES].mean(axis=1)
  wide[PESO_LABEL] = wide[PESO_KEY[0]]
  return wide[["SCHEDA", PESO_LABEL] + PLICHE_NAMES + [MEDIA_LABEL]]


def render(allowed_athletes):
  """Disegna la pagina Pliche Cutanee."""
  col_h1, col_h2 = st.columns([8, 2])
  with col_h1:
    st.markdown("### 📏 **Pliche Cutanee** — Peso, pliche e andamento")
  with col_h2:
    if st.button("🏠 Torna alla Home", use_container_width=True):
      st.session_state.page = "home"
      st.rerun()

  if allowed_athletes == "ALL":
    st.sidebar.success("🔓 Visualizzazione: Roster Completo")
    # Il link al foglio completo (dati di tutti) solo nella vista completa
    st.link_button(T("📂 Apri il Google Sheet delle pliche"), PLICHE_SHEET_URL)
  else:
    st.sidebar.success(f"🔓 Visualizzazione Dedicata: {allowed_athletes[0]}")

  df_all, diag, raw, error = load_pliche_data()

  def diagnostics():
    if allowed_athletes != "ALL" or diag.empty:
      return
    with st.expander("🔧 Diagnostica lettura del foglio"):
      st.dataframe(diag, use_container_width=True, hide_index=True)
      if raw:
        tab = st.selectbox("Scheda da controllare", list(raw), key="pliche_raw_tab")
        st.dataframe(raw[tab], use_container_width=True)

  if error:
    st.info(f"ℹ️ Impossibile leggere il foglio delle pliche: {error}")
    return
  if df_all.empty:
    st.info("ℹ️ Nel foglio non ho trovato dati di pliche leggibili.")
    diagnostics()
    return

  if allowed_athletes != "ALL":
    df_all = df_all[df_all["ATHLETE"].isin(allowed_athletes)]
    if df_all.empty:
      st.info("ℹ️ Nessun dato di pliche per questo giocatore.")
      return
    players = list(allowed_athletes)
  else:
    available = sorted(
        (p for p in ruoli_dict if p in set(df_all["ATHLETE"])), key=_label
    )
    players = st.multiselect(
        "Seleziona i giocatori",
        available,
        default=available[:1],
        format_func=_label,
        key="pliche_players",
    )
    if not players:
      st.info("ℹ️ Seleziona almeno un giocatore.")
      diagnostics()
      return

  for p in players:
    d = df_all[df_all["ATHLETE"] == p]
    st.markdown(f"#### {_label(p)} — {ruoli_dict.get(p, '')}")
    if d.empty:
      st.info("ℹ️ Nessun dato di pliche per questo giocatore.")
      continue
    wide = _player_table(d)

    show = wide.rename(columns={"SCHEDA": "Data"}).set_index("Data")
    st.dataframe(show.round(1), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
      st.markdown("**⚖️ Andamento del peso**")
      if wide[PESO_LABEL].notna().any():
        st.altair_chart(
            _trend_chart(wide, PESO_LABEL, "Peso (kg)", PESO_COLOR),
            use_container_width=True,
        )
      else:
        st.caption("Nessun dato di peso per questo giocatore.")
    with c2:
      st.markdown("**📉 Andamento della media delle pliche**")
      if wide[MEDIA_LABEL].notna().any():
        st.altair_chart(
            _trend_chart(wide, MEDIA_LABEL, "Media pliche (mm)", MEDIA_COLOR),
            use_container_width=True,
        )
      else:
        st.caption("Nessun dato di pliche per questo giocatore.")

  st.caption(
      "La media è calcolata sulle pliche rilevate in ogni data."
      " Sono mostrate solo le date con dati."
  )
  diagnostics()
