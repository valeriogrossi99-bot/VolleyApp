import glob
import os
import altair as alt
import pandas as pd
import streamlit as st

# 1. Configurazione della Pagina con Sidebar Visibile di Default
st.set_page_config(
    page_title="Cuneo Volley Performance Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. CSS Personalizzato - PULSANTE SIDEBAR SEMPRE VISIBILE
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
    /* Rimozione footer ed elementi inutili SENZA nascondere il bottone della Sidebar */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Assicura che il pulsante per aprire la sidebar sia sempre ben visibile */
    button[data-testid="stHeaderIconButton"] {
        visibility: visible !important;
        display: block !important;
    }

    .stApp {
        background-color: #ffffff;
        color: #1f2937;
    }

    /* Centratura Logo Home */
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

    /* TRASFORMAZIONE PULSANTI HOME IN CARD CLICCABILI */
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

# 3. Inizializzazione Sessione Navigazione
if "page" not in st.session_state:
  st.session_state.page = "home"

# 4. Roster Ufficiale e Info Giocatori
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


def get_custom_week(dt_series):
  days_diff = (dt_series - ANCHOR_MONDAY).dt.days
  week_offset = days_diff // 7
  custom_week_num = 7 + week_offset
  return "Settimana " + custom_week_num.astype(str)


def extract_week_num(w_str):
  try:
    return int(w_str.replace("Settimana ", ""))
  except Exception:
    return 0


# 5. Mappatura Codici Accesso Riservato
ACCESS_CODES = {
    "CUNEO": "ALL",
    "FRA-CN": ["Nathan Feral"],
    "ITA-CN": ["Leandro Mosca"],
}


def render_access_control():
  st.sidebar.header("🔑 Accesso Riservato")
  code_in = st.sidebar.text_input(
      "Inserisci Codice PIN:", type="password"
  ).strip()

  if code_in in ACCESS_CODES:
    allowed = ACCESS_CODES[code_in]
    if allowed == "ALL":
      st.sidebar.success("🔓 Accesso Completo: Roster Cuneo Volley")
    else:
      st.sidebar.success(f"🔓 Accesso Riservato: {', '.join(allowed)}")
    return allowed
  else:
    if code_in != "":
      st.sidebar.error("❌ Codice Errato")
    return "ALL"


# 6. Funzioni Caricamento Dati
@st.cache_data
def load_jump_data():
  files = glob.glob("data/*.csv") + glob.glob("*.csv")
  df_list = []
  for f in files:
    try:
      temp = pd.read_csv(f, sep=";")
      if "JUMP HEIGHT(cm)" in temp.columns:
        df_list.append(temp)
    except Exception:
      pass

  if not df_list:
    return pd.DataFrame()

  df = pd.concat(df_list, ignore_index=True)
  df.columns = df.columns.str.strip()

  df["ATHLETE"] = (
      df["NAME"].astype(str).str.strip()
      + " "
      + df["SURNAME"].astype(str).str.strip()
  )
  df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")
  df["DATE_DT"] = pd.to_datetime(df["DATE"], errors="coerce")
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


@st.cache_data
def load_load_data():
  files = glob.glob("data/*.csv") + glob.glob("*.csv")
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
  elif "ATHLETE" not in df.columns:
    df["ATHLETE"] = "Atleta Generico"

  df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")

  date_col = "DATE" if "DATE" in df.columns else "Data"
  df["DATE_DT"] = pd.to_datetime(df[date_col], errors="coerce")
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


# ==============================================================================
# SCHERMATA 1: HOME PAGE GENERALE
# ==============================================================================
if st.session_state.page == "home":
  st.markdown(
      """
        <div class="logo-container">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10" width="140">
        </div>
        <h1 style="text-align: center; font-size: 2.8rem; margin-top: 10px; margin-bottom: 5px;">Cuneo Volley</h1>
        <p style="text-align: center; color: #64748b; font-size: 1.1rem; font-weight: 500; margin-bottom: 40px;">Performance & Analytics Hub</p>
    """,
      unsafe_allow_html=True,
  )

  col_card1, col_card2 = st.columns(2)

  with col_card1:
    btn_datajump = st.button(
        "🚀\n\nDataJump\n\nMonitoraggio Salti, Elevazione & Distribuzione"
        " Fasce",
        key="btn_jump",
        use_container_width=True,
    )
    if btn_datajump:
      st.session_state.page = "datajump"
      st.rerun()

  with col_card2:
    btn_dataload = st.button(
        "🏋️‍♂️\n\nDataLoad\n\nMonitoraggio Carichi Sala Pesi & Tonnellaggio",
        key="btn_load",
        use_container_width=True,
    )
    if btn_dataload:
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

  # Controllo Accessi e Filtri Sidebar
  allowed_athletes = render_access_control()

  df_jump = load_jump_data()

  if df_jump.empty:
    st.warning(
        "⚠️ Nessun file CSV relativo ai salti trovato. Carica i file contenenti"
        " 'JUMP HEIGHT(cm)' nella cartella 'data/'."
    )
    st.stop()

  # Filtro sicurezza in base al codice PIN
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

  # Player Card
  if selected_players:
    if len(selected_players) == 1:
      p = selected_players[0]
      role_val = ruoli_dict.get(p, "Atleta")
      details = player_info.get(p, {})
      bio_val = details.get("bio", "Cuneo Volley Prima Squadra")
      link_val = details.get(
          "url", "https://cuneovolley.it/prima-squadra/giocatori"
      )

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
    else:
      st.info(
          f"📊 **Modalità Confronto Attiva**: Stai confrontando **{len(selected_players)} giocatori** ({', '.join(selected_players)})."
      )

  # Summaries
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

  # KPI
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

  tab1, tab2, tab3, tab4 = st.tabs([
      "📊 Andamento Giornaliero",
      "🗓️ Andamento Settimanale",
      "⚔️ Confronto Giocatori",
      "🎯 Distribuzione Fasce",
  ])

  with tab1:
    if not daily_summary.empty:
      st.markdown("##### 🔵 Volume Salti per Data e Giocatore")
      chart1 = (
          alt.Chart(daily_summary)
          .mark_bar()
          .encode(
              x=alt.X("DATE_STR:N", title="Data Seduta"),
              y=alt.Y("SALTI_GIORNO:Q", title="Nr. Salti"),
              color=alt.Color("ATHLETE:N", title="Giocatore"),
              tooltip=["DATE_STR", "ATHLETE", "SALTI_GIORNO", "MAX_GIORNO"],
          )
          .properties(height=380)
      )
      st.altair_chart(chart1, use_container_width=True)

      st.markdown("##### 🚀 Salto Max (cm)")
      chart2 = (
          alt.Chart(daily_summary)
          .mark_line(point=True)
          .encode(
              x=alt.X("DATE_STR:N", title="Data Seduta"),
              y=alt.Y("MAX_GIORNO:Q", title="Salto Max (cm)"),
              color=alt.Color("ATHLETE:N", title="Giocatore"),
              tooltip=["DATE_STR", "ATHLETE", "MAX_GIORNO"],
          )
          .properties(height=380)
      )
      st.altair_chart(chart2, use_container_width=True)

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

# ==============================================================================
# SCHERMATA 3: MODULO DATALOAD
# ==============================================================================
elif st.session_state.page == "dataload":
  col_h1, col_h2 = st.columns([8, 2])
  with col_h1:
    st.markdown("### 🏋️‍♂️ **DataLoad** — Monitoraggio Carichi Sala Pesi")
  with col_h2:
    if st.button("🏠 Torna alla Home", use_container_width=True):
      st.session_state.page = "home"
      st.rerun()

  # Controllo Accessi e Filtri Sidebar
  allowed_athletes = render_access_control()

  df_load = load_load_data()

  if df_load.empty:
    st.info(
        "ℹ️ Nessun file CSV relativo alla sala pesi caricato in 'data/'. Carica"
        " file CSV contenenti dati di tonnellaggio/carichi per visualizzare le"
        " analisi."
    )
    st.stop()

  # Filtro sicurezza in base al codice PIN
  if allowed_athletes != "ALL":
    df_load = df_load[df_load["ATHLETE"].isin(allowed_athletes)]

  st.sidebar.divider()
  st.sidebar.header("🔍 Filtri Selezione & Confronto")

  ruoli_list = sorted(list(set(df_load["ROLE"].unique())))
  selected_roles = st.sidebar.multiselect("Filtra per Ruolo", ruoli_list)

  df_f = df_load.copy()
  if selected_roles:
    df_f = df_f[df_f["ROLE"].isin(selected_roles)]

  giocatori_list = sorted(df_f["ATHLETE"].unique())
  selected_players = st.sidebar.multiselect(
      "Seleziona Giocatori da Analizzare / Confrontare", giocatori_list
  )

  if selected_players:
    df_f = df_f[df_f["ATHLETE"].isin(selected_players)]

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

  # Player Card
  if selected_players:
    if len(selected_players) == 1:
      p = selected_players[0]
      role_val = ruoli_dict.get(p, "Atleta")
      details = player_info.get(p, {})
      bio_val = details.get("bio", "Cuneo Volley Prima Squadra")
      link_val = details.get(
          "url", "https://cuneovolley.it/prima-squadra/giocatori"
      )

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
    else:
      st.info(
          f"📊 **Modalità Confronto Attiva**: Stai confrontando **{len(selected_players)} giocatori** ({', '.join(selected_players)})."
      )

  # Summaries Sala Pesi
  load_daily = (
      df_f.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"])
      .agg(
          TONNELLAGGIO_GIORNO=("TOTAL_LOAD", "sum"),
          CARICO_MAX=("TOTAL_LOAD", "max"),
      )
      .reset_index()
  )

  load_weekly = (
      df_f.groupby(["ATHLETE", "ROLE", "WEEK"])
      .agg(
          TONNELLAGGIO_SETTIMANA=("TOTAL_LOAD", "sum"),
          CARICO_MAX_SETTIMANA=("TOTAL_LOAD", "max"),
      )
      .reset_index()
  )

  # KPI Sala Pesi
  c1, c2, c3, c4 = st.columns(4)
  c1.metric(
      "Tonnellaggio Totale",
      f"{load_daily['TONNELLAGGIO_GIORNO'].sum():,.0f} kg",
  )
  c2.metric(
      "Carico Max Sollevato",
      f"{load_daily['CARICO_MAX'].max() if not load_daily.empty else 0:,.0f} kg",
  )
  c3.metric(
      "Media Tonnellaggio / Seduta",
      f"{load_daily['TONNELLAGGIO_GIORNO'].mean() if not load_daily.empty else 0:,.0f} kg",
  )
  c4.metric(
      "Giocatori Monitorati",
      f"{len(df_f['ATHLETE'].unique()) if not df_f.empty else 0}",
  )

  st.divider()

  tab1, tab2, tab3 = st.tabs([
      "📊 Tonnellaggio Giornaliero",
      "🗓️ Carico Settimanale",
      "⚔️ Confronto Carichi Atleti",
  ])

  with tab1:
    if not load_daily.empty:
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

  with tab2:
    if not load_weekly.empty:
      st.markdown("##### 🗓️ Tonnellaggio Settimanale per Giocatore (kg)")
      chart_lw = (
          alt.Chart(load_weekly)
          .mark_bar()
          .encode(
              x=alt.X("WEEK:N", title="Settimana"),
              y=alt.Y(
                  "TONNELLAGGIO_SETTIMANA:Q", title="Tonnellaggio Settimanale (kg)"
              ),
              color=alt.Color("ATHLETE:N", title="Giocatore"),
              tooltip=["WEEK", "ATHLETE", "SALTI_SETTIMANA" if "SALTI_SETTIMANA" in load_weekly.columns else "TONNELLAGGIO_SETTIMANA"],
          )
          .properties(height=380)
      )
      st.altair_chart(chart_lw, use_container_width=True)

  with tab3:
    if not df_f.empty:
      comp_load = (
          df_f.groupby(["ATHLETE", "ROLE"])
          .agg(
              TOT_TONN=("TOTAL_LOAD", "sum"),
              MAX_TONN=("TOTAL_LOAD", "max"),
          )
          .reset_index()
      )
      col_x, col_y = st.columns(2)
      with col_x:
        st.write("**Volume Totale Sollevato (kg) per Giocatore**")
        st.altair_chart(
            alt.Chart(comp_load)
            .mark_bar(color="#2563eb")
            .encode(
                x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                y=alt.Y("TOT_TONN:Q", title="Volume Totale (kg)"),
                tooltip=["ATHLETE", "TOT_TONN"],
            )
            .properties(height=350),
            use_container_width=True,
        )
      with col_y:
        st.write("**Carico Picco Sollevato (kg) per Giocatore**")
        st.altair_chart(
            alt.Chart(comp_load)
            .mark_bar(color="#f97316")
            .encode(
                x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                y=alt.Y("MAX_TONN:Q", title="Picco Carico (kg)"),
                tooltip=["ATHLETE", "MAX_TONN"],
            )
            .properties(height=350),
            use_container_width=True,
        )

  with st.expander("📋 Tabella Dati Completi Pesi"):
    st.dataframe(df_f, use_container_width=True)
