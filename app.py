import glob
import os
import altair as alt
import pandas as pd
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
    </style>
""",
    unsafe_allow_html=True,
)

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
    link_val = details.get("url", "https://cuneovolley.it/prima-squadra/giocatori")

    st.markdown(
        f"""
        <div class="player-card">
            <div class="player-title">🛡️ {p}</div>
            <div class="player-role">Ruolo: {role_val}</div>
            <p style="color: #475569; margin-top: 8px; margin-bottom: 12px;">{bio_val}</p>
            <a href="{link_val}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 600;">🔗 Vai alla scheda ufficiale Cuneo Volley &rarr;</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
      st.markdown("##### 🔵 Volume Salti per Data e Giocatore")
      match_dates = daily_summary[daily_summary["IS_MATCH"].astype(bool)][
          ["DATE_STR"]
      ].drop_duplicates()
      bars1 = (
          alt.Chart(daily_summary)
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

      st.markdown("##### 🚀 Salto Max (cm)")
      line2 = (
          alt.Chart(daily_summary)
          .mark_line(point=True)
          .encode(
              x=alt.X("DATE_STR:N", title="Data Seduta"),
              y=alt.Y("MAX_GIORNO:Q", title="Salto Max (cm)"),
              color=alt.Color("ATHLETE:N", title="Giocatore"),
              tooltip=["DATE_STR", "ATHLETE", "MAX_GIORNO"],
          )
      )
      match_pts = daily_summary[daily_summary["IS_MATCH"].astype(bool)]
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

        date_disponibili = sorted(df_session_seq["DATE_STR"].unique())

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

  if allowed_athletes != "ALL":
    if not df_load.empty:
      df_load = df_load[df_load["ATHLETE"].isin(allowed_athletes)]
    if not df_force.empty:
      df_force = df_force[df_force["ATHLETE"].isin(allowed_athletes)]

  st.sidebar.divider()
  st.sidebar.header("🔍 Filtri Selezione & Confronto")

  tab_force_eval, tab1 = st.tabs([
      "🏋️ Valutazione Forza & 1RM (Google Sheet)",
      "📊 Tonnellaggio & Volume Pesi",
  ])

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
