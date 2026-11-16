"""pliche.py — sezione Pliche Cutanee (plicometria).

Il Google Sheet "Antropometria Cuneo" ha una scheda per ogni data (nome della
scheda in formato gg/mm, ad es. "24/08", oppure "20-22/10" se la misurazione è
su più giorni). Per ogni scheda l'app cerca il nome di ogni giocatore, riconosce
dove sono i suoi dati e legge le 6 pliche (tricipite, sottoscapolare, obliquo,
addominale, quadricipite, polpaccio). Poi disegna un grafico per giocatore con
l'andamento di ogni plica e la media delle pliche.

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
PLICHE_NAMES = [n for n, _ in PLICHE_KEYS]
KEY_TO_NAME = {k: n for n, k in PLICHE_KEYS}
MEDIA_LABEL = "Media pliche"
PLICHE_COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#db2777", "#7c3aed", "#0891b2"]
MEDIA_COLOR = "#0f172a"

# Nome scheda = data: "24/08", "13/11", "20-22/10", "27-29/10"
TAB_DATE_RX = re.compile(r"^\s*(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?\s*/\s*(\d{1,2})\s*$")
NUM_RX = re.compile(r"^\s*(-?\d+(?:[.,]\d+)?)\s*(?:mm)?\s*$", re.I)
# Se il giocatore ha più misure vicine (2-3 rilevazioni), le leggo e ne faccio la media
MAX_COLS_PER_PLAYER = 6

_NEW_EN = {
    "### 📏 **Pliche Cutanee** — Andamento per giocatore": (
        "### 📏 **Skinfolds** — Trend by player"
    ),
    "Plicometria & Composizione Corporea": "Skinfolds & Body Composition",
    "📂 Apri il Google Sheet delle pliche": "📂 Open the skinfolds Google Sheet",
    "ℹ️ Nel foglio non ho trovato dati di pliche leggibili.": (
        "ℹ️ No readable skinfold data found in the sheet."
    ),
    "ℹ️ Nessun dato di pliche per questo giocatore.": (
        "ℹ️ No skinfold data for this player."
    ),
    "Pliche Cutanee": "Skinfolds",
    "Filtra per Giocatore": "Filter by Player",
    "Media pliche": "Skinfold average",
    "Plica (mm)": "Skinfold (mm)",
    "Media pliche (mm)": "Skinfold average (mm)",
    "Media (mm)": "Average (mm)",
    "Plica": "Skinfold",
    "Data": "Date",
    "Tricipite": "Triceps",
    "Sottoscapolare": "Subscapular",
    "Obliquo": "Oblique",
    "Addominale": "Abdominal",
    "Quadricipite": "Quadriceps",
    "Polpaccio": "Calf",
    "📋 Valori (mm)": "📋 Values (mm)",
    "##### 👥 Media pliche — confronto squadra": (
        "##### 👥 Skinfold average — team comparison"
    ),
    "La media è calcolata sulle pliche rilevate in ogni data.": (
        "The average is calculated on the skinfolds measured on each date."
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


def _num(text):
  m = NUM_RX.match(str(text))
  if not m:
    return None
  try:
    v = float(m.group(1).replace(",", "."))
  except ValueError:
    return None
  return v if 0 < v <= 100 else None


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
  labs = {key: [] for _, key in PLICHE_KEYS}
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
        for _, key in PLICHE_KEYS:
          if s.startswith(key):
            labs[key].append((r, c))
            break
  return labs, heads


def _orientation(labs):
  """'V' = nomi delle pliche in colonna (giocatori affiancati); 'H' = in riga."""
  pos = [max(v) for v in labs.values() if v]
  if len(pos) < 2:
    return "V"
  rows = {p[0] for p in pos}
  cols = {p[1] for p in pos}
  return "V" if len(rows) >= len(cols) else "H"


def _parse_tab(g, pkeys):
  """Legge una scheda: {(giocatore, plica): (distanza, valore medio, n)}."""
  labs, heads = _labels(g)
  orient = "V"
  if any(labs.values()):
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
    for _, key in PLICHE_KEYS:
      cands = [
          q for q in labs[key]
          if ar < q[0] < limit and (hdr is None or q[0] > hdr)
      ]
      if not cands:
        continue
      lr, lc = min(cands) if hdr is not None else max(cands)
      vals = [_num(g[lr, c]) for c in range(ac, cend) if c != lc]
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
                   "Disposizione": "", "Giocatori trovati": 0, "Valori letti": 0})
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
    })
  df_long = pd.DataFrame(rows)
  return df_long, pd.DataFrame(diag), raw, None


# ------------------------------------------------------------------------------
# Grafici
# ------------------------------------------------------------------------------
def _player_chart(d_long, d_mean, order):
  """Una linea per ogni plica + linea tratteggiata scura per la media."""
  data = pd.concat(
      [d_long[["SCHEDA", "PLICA", "VALORE"]], d_mean], ignore_index=True
  )
  color = alt.Color(
      "PLICA:N",
      title="Plica",
      scale=alt.Scale(
          domain=PLICHE_NAMES + [MEDIA_LABEL],
          range=PLICHE_COLORS + [MEDIA_COLOR],
      ),
  )
  base = alt.Chart(data).encode(
      x=alt.X("SCHEDA:N", title="Data", sort=order, axis=alt.Axis(labelAngle=0)),
      y=alt.Y("VALORE:Q", title="Plica (mm)", scale=alt.Scale(zero=False)),
      color=color,
      tooltip=[
          alt.Tooltip("SCHEDA:N", title="Data"),
          alt.Tooltip("PLICA:N", title="Plica"),
          alt.Tooltip("VALORE:Q", title="mm", format=".1f"),
      ],
  )
  lines = base.transform_filter(alt.datum.PLICA != MEDIA_LABEL).mark_line(
      point=True
  )
  media = base.transform_filter(alt.datum.PLICA == MEDIA_LABEL).mark_line(
      point=alt.OverlayMarkDef(size=90), strokeWidth=4, strokeDash=[6, 4]
  )
  return alt.layer(lines, media).properties(height=320)


def _team_chart(df_mean_all, order):
  return (
      alt.Chart(df_mean_all)
      .mark_line(point=True)
      .encode(
          x=alt.X("SCHEDA:N", title="Data", sort=order, axis=alt.Axis(labelAngle=0)),
          y=alt.Y("VALORE:Q", title="Media pliche (mm)", scale=alt.Scale(zero=False)),
          color=alt.Color("ATHLETE:N", title="Giocatore"),
          tooltip=[
              alt.Tooltip("SCHEDA:N", title="Data"),
              alt.Tooltip("ATHLETE:N", title="Giocatore"),
              alt.Tooltip("VALORE:Q", title="Media (mm)", format=".1f"),
          ],
      )
      .properties(height=360)
  )


# ------------------------------------------------------------------------------
# Pagina
# ------------------------------------------------------------------------------
def render(allowed_athletes):
  """Disegna la pagina Pliche Cutanee."""
  col_h1, col_h2 = st.columns([8, 2])
  with col_h1:
    st.markdown("### 📏 **Pliche Cutanee** — Andamento per giocatore")
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

  # Ordine cronologico delle schede (date)
  order = (
      df_all.drop_duplicates("SCHEDA").sort_values("DATA")["SCHEDA"].tolist()
  )

  players = sorted(df_all["ATHLETE"].unique())
  if allowed_athletes == "ALL":
    st.sidebar.divider()
    st.sidebar.header("🔍 Filtri Selezione & Confronto")
    selected = st.sidebar.multiselect("Filtra per Giocatore", players)
    if selected:
      players = [p for p in players if p in selected]

  # Media delle pliche per giocatore e data
  mean_all = (
      df_all.groupby(["ATHLETE", "SCHEDA"], as_index=False)["VALORE"].mean()
  )

  if allowed_athletes == "ALL" and len(players) > 1 and len(order) > 1:
    st.markdown("##### 👥 Media pliche — confronto squadra")
    st.altair_chart(
        _team_chart(mean_all[mean_all["ATHLETE"].isin(players)], order),
        use_container_width=True,
    )

  for p in players:
    d_long = df_all[df_all["ATHLETE"] == p]
    d_mean = (
        d_long.groupby("SCHEDA", as_index=False)["VALORE"].mean()
        .assign(PLICA=MEDIA_LABEL)
    )
    p_order = [t for t in order if t in set(d_long["SCHEDA"])]

    st.markdown(f"#### {p} — {ruoli_dict.get(p, '')}")
    st.altair_chart(_player_chart(d_long, d_mean, p_order), use_container_width=True)

    with st.expander("📋 Valori (mm)"):
      piv = d_long.pivot_table(
          index="PLICA", columns="SCHEDA", values="VALORE", aggfunc="mean"
      )
      piv = piv.reindex(
          index=[n for n in PLICHE_NAMES if n in piv.index], columns=p_order
      )
      piv.loc[MEDIA_LABEL] = piv.mean(axis=0)
      st.dataframe(piv.round(1), use_container_width=True)

  st.caption("La media è calcolata sulle pliche rilevate in ogni data.")
  if allowed_athletes == "ALL":
    missing = [p for p in ruoli_dict if p not in set(df_all["ATHLETE"])]
    if missing:
      st.caption(f"Nessun dato per: {', '.join(missing)}")
  diagnostics()
