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

# 3. Inizializzazione Sessione e Autenticazione
if "page" not in st.session_state:
  st.session_state.page = "home"

if "auth_token" not in st.session_state:
  st.session_state.auth_token = None

if "pending_module" not in st.session_state:
  st.session_state.pending_module = None

# Database in memoria di sessione per le modifiche rapide da app
if "local_force_db" not in st.session_state:
  st.session_state.local_force_db = pd.DataFrame(
      columns=[
          "ATHLETE",
          "ESERCIZIO",
          "BW",
          "Peso usato",
          "Reps",
          "RIR",
          "1RM Teorico",
          "1RM/BW",
      ]
  )

ACCESS_CODES = {
    "CUNEO": "ALL",
    "FRACN": ["Nathan Feral"],
    "ITA-CN": ["Leandro Mosca"],
}

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

PESI_CORPOREI_DEFAULT = {
    "Bryan Argilagos": 84.0,
    "Manuel Coscione": 85.0,
    "Alexandre Strehlau": 91.0,
    "Ethan Champlin": 88.0,
    "Federico Giraudo": 82.0,
    "Poriya Khanzadeh": 95.0,
    "Nathan Feral": 97.0,
    "Lorenzo Sala": 97.0,
    "Emanuele Barberio": 88.0,
    "Leandro Mosca": 102.0,
    "Lorenzo Codarin": 92.0,
    "Nicoló Volpe": 85.0,
    "Mimmo Cavaccini": 68.0,
    "Thibault Loubeyre": 77.0,
}

player_info = {
    "Nathan Feral": {
        "bio": "Opposto | Altezza: 197 cm | Classe 2003",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Leandro Mosca": {
        "bio": "Centrale | Altezza: 209 cm | Classe 2000",
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
  return "Settimana " + (7 + week_offset).astype(str)


def extract_week_num(w_str):
  try:
    return int(w_str.replace("Settimana ", ""))
  except Exception:
    return 0


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
  else:
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

  if st.session_state.pending_module:
    st.warning(
        f"🔑 **Inserisci il codice PIN di accesso per proseguire verso"
        f" {st.session_state.pending_module.upper()}**"
    )
    col_pin, col_btn = st.columns([3, 1])
    with col_pin:
      entered_pin = st.text_input(
          "Codice di Sicurezza:", type="password", key="pin_input"
      ).strip()
    with col_btn:
      st.write("")
      st.write("")
      if st.button("Conferma PIN 🔓", use_container_width=True):
        if entered_pin in ACCESS_CODES:
          st.session_state.auth_token = entered_pin
          st.session_state.page = st.session_state.pending_module
          st.session_state.pending_module = None
          st.rerun()
        else:
          st.error("❌ Codice non valido. Riprova.")
    if st.button("❌ Annulla", use_container_width=False):
      st.session_state.pending_module = None
      st.rerun()
  else:
    col_card1, col_card2 = st.columns(2)
    with col_card1:
      if st.button(
          "🚀\n\nDataJump\n\nMonitoraggio Salti, Elevazione & Fasce",
          key="btn_jump",
          use_container_width=True,
      ):
        if st.session_state.auth_token is not None:
          st.session_state.page = "datajump"
          st.rerun()
        else:
          st.session_state.pending_module = "datajump"
          st.rerun()
    with col_card2:
      if st.button(
          "🏋️‍♂️\n\nDataLoad\n\nMonitoraggio Carichi, Massimali & Inserimento"
          " Rapido",
          key="btn_load",
          use_container_width=True,
      ):
        if st.session_state.auth_token is not None:
          st.session_state.page = "dataload"
          st.rerun()
        else:
          st.session_state.pending_module = "dataload"
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

  token = st.session_state.auth_token
  allowed_athletes = ACCESS_CODES.get(token, "ALL")
  if allowed_athletes == "ALL":
    st.sidebar.success("🔓 Accesso Completo: Roster Cuneo Volley")
  else:
    st.sidebar.success(f"🔓 Accesso Riservato: {', '.join(allowed_athletes)}")

  df_jump = load_jump_data()
  if df_jump.empty:
    st.warning(
        "⚠️ Nessun file CSV relativo ai salti trovato nella cartella 'data/'."
    )
    st.stop()

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

# ==============================================================================
# SCHERMATA 3: MODULO DATALOAD CON INSERIMENTO RAPIDO DA APP
# ==============================================================================
elif st.session_state.page == "dataload":
  col_h1, col_h2 = st.columns([8, 2])
  with col_h1:
    st.markdown("### 🏋️‍♂️ **DataLoad** — Carichi, Massimali & Inserimento Rapido")
  with col_h2:
    if st.button("🏠 Torna alla Home", use_container_width=True):
      st.session_state.page = "home"
      st.rerun()

  token = st.session_state.auth_token
  allowed_athletes = ACCESS_CODES.get(token, "ALL")

  if allowed_athletes == "ALL":
    st.sidebar.success("🔓 Accesso Completo: Roster Cuneo Volley")
  else:
    st.sidebar.success(f"🔓 Accesso Riservato: {', '.join(allowed_athletes)}")

  df_load = load_load_data()
  if allowed_athletes != "ALL" and not df_load.empty:
    df_load = df_load[df_load["ATHLETE"].isin(allowed_athletes)]

  # Tab per separare Inserimento Rapido, Valutazione Forza e Tonnellaggio
  tab_fast, tab_force_eval, tab1 = st.tabs([
      "✏️ Inserimento Rapido (Da App)",
      "🏋️ Tabella & Grafici Forza",
      "📊 Tonnellaggio & Volume Pesi",
  ])

  with tab_fast:
    st.markdown(
        "##### ⚡ Inserisci o Aggiorna i Dati di Forza direttamente dall'App"
    )
    st.info(
        "Compila i campi sottostanti per registrare la performance dell'atleta."
        " Il massimale teorico (1RM) e la forza relativa verranno calcolati"
        " automaticamente all'istante."
    )

    with st.form("form_inserimento_forza"):
      col_f1, col_f2 = st.columns(2)
      with col_f1:
        atleta_sel = st.selectbox(
            "Seleziona Atleta",
            list(ruoli_dict.keys())
            if allowed_athletes == "ALL"
            else allowed_athletes,
        )
        esercizio_sel = st.selectbox(
            "Esercizio", ["Back Squat", "Front Squat", "Stacco QB"]
        )
      with col_f2:
        peso_usato = st.number_input(
            "Peso Usato (kg)", min_value=0.0, max_value=300.0, value=100.0, step=1.0
        )
        reps = st.number_input(
            "Ripetizioni Eseguite", min_value=1, max_value=20, value=3, step=1
        )
        rir = st.number_input(
            "RIR (Ripetizioni in Riserva)",
            min_value=0,
            max_value=5,
            value=1,
            step=1,
        )

      submitted = st.form_submit_button("Salva e Calcola 💾")
      if submitted:
        bw = PESI_CORPOREI_DEFAULT.get(atleta_sel, 85.0)
        # Calcolo 1RM Teorico con Formula Epley corretta per RIR
        rm_teorico = peso_usato * (1 + (reps + rir) / 30)
        forza_relativa = rm_teorico / bw

        # Rimuoviamo eventuale record precedente per lo stesso atleta ed esercizio
        db = st.session_state.local_force_db
        db = db[
            ~(
                (db["ATHLETE"] == atleta_sel)
                & (db["ESERCIZIO"] == esercizio_sel)
            )
        ]

        # Aggiungiamo il nuovo record
        nuova_riga = pd.DataFrame([{
            "ATHLETE": atleta_sel,
            "ESERCIZIO": esercizio_sel,
            "BW": bw,
            "Peso usato": peso_usato,
            "Reps": reps,
            "RIR": rir,
            "1RM Teorico": round(rm_teorico, 1),
            "1RM/BW": round(forza_relativa, 2),
        }])

        st.session_state.local_force_db = pd.concat(
            [db, nuova_riga], ignore_index=True
        )
        st.success(
            f"✅ Salvato! 1RM Teorico calcolato per {atleta_sel}:"
            f" **{round(rm_teorico, 1)} kg** (Forza Relativa:"
            f" **{round(forza_relativa, 2)} xBW**)"
        )

    # Mostra la tabella dei dati salvati localmente
    if not st.session_state.local_force_db.empty:
      st.markdown("---")
      st.markdown("##### 📋 Dati di Forza Inseriti nella Sessione Corrente")
      st.dataframe(
          st.session_state.local_force_db, use_container_width=True
      )

      if st.button("🗑️ Pulisci Tabella Inserimenti"):
        st.session_state.local_force_db = pd.DataFrame(
            columns=[
                "ATHLETE",
                "ESERCIZIO",
                "BW",
                "Peso usato",
                "Reps",
                "RIR",
                "1RM Teorico",
                "1RM/BW",
            ]
        )
        st.rerun()

  with tab_force_eval:
    st.markdown("##### 🏋️‍♂️ Analisi Massimali & Forza Relativa")
    df_f_local = st.session_state.local_force_db

    if not df_f_local.empty:
      selected_ex = st.selectbox(
          "Filtra Esercizio per Grafico:", df_f_local["ESERCIZIO"].unique()
      )
      df_ex_sub = df_f_local[df_f_local["ESERCIZIO"] == selected_ex]

      col_g1, col_g2 = st.columns(2)
      with col_g1:
        st.write(f"**1RM Teorico (kg) — {selected_ex}**")
        chart_1rm = (
            alt.Chart(df_ex_sub)
            .mark_bar(color="#2563eb")
            .encode(
                x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                y=alt.Y("1RM Teorico:Q", title="1RM Teorico (kg)"),
                tooltip=["ATHLETE", "Peso usato", "Reps", "1RM Teorico"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_1rm, use_container_width=True)

      with col_g2:
        st.write(f"**Forza Relativa (1RM / BW) — {selected_ex}**")
        chart_fr = (
            alt.Chart(df_ex_sub)
            .mark_bar(color="#16a34a")
            .encode(
                x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                y=alt.Y("1RM/BW:Q", title="Forza Relativa (xBW)"),
                tooltip=["ATHLETE", "BW", "1RM/BW"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_fr, use_container_width=True)
    else:
      st.info(
          "ℹ️ Non ci sono ancora dati inseriti. Usa il tab 'Inserimento"
          " Rapido' per aggiungere i primi carichi."
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
      st.info("ℹ️ Nessun dato di tonnellaggio giornaliero disponibile.")
