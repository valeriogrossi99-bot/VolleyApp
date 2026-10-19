import glob
import os
import altair as alt
import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="DataJump - Cuneo Volley",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <head>
        <link rel="manifest" href="manifest.json">
        <meta name="theme-color" content="#2563eb">
        <meta name="apple-mobile-web-app-capable" yes>
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <link rel="apple-touch-icon" href="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10">
    </head>
""",
    unsafe_allow_html=True,
)

# --- CSS PERSONALIZZATO CON SFONDO BIANCO E COLORI CUNEO VOLLEY ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #ffffff;
        color: #1f2937;
    }
    .header-container {
        display: flex;
        align-items: center;
        gap: 20px;
        padding-bottom: 12px;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 25px;
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
    h1, h2, h3 {
        color: #0f172a;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- HEADER UFFICIALE CON STEMMA E TITOLO DATAJUMP ---
col_shield, col_title = st.columns([1, 10])
with col_shield:
  st.image(
      "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10",
      width=70,
  )
with col_title:
  st.markdown(
      """
        <h1 style="margin: 0; font-size: 2.5rem; color: #0f172a; letter-spacing: 1px;">DataJump</h1>
        <p style="margin: 0; color: #475569; font-size: 1rem;">Cuneo Volley — Dashboard Ufficiale Monitoraggio Salti & Carichi (Sola Lettura)</p>
    """,
      unsafe_allow_html=True,
  )

# --- ROSTER UFFICIALE E RUOLI ---
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


@st.cache_data
def load_all_sessions():
  files = glob.glob("data/*.csv") + glob.glob("*.csv")
  if not files:
    return pd.DataFrame()

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

  # Categorizzazione delle fasce di salto
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


df = load_all_sessions()

if df.empty:
  st.warning(
      "⚠️ Nessun file CSV valido trovato. Carica i file nella cartella 'data/'"
      " su GitHub."
  )
  st.stop()

# --- BARRA LATERALE: FILTRI ---
st.sidebar.header("🔍 Filtri Selezione")

ruoli_list = ["Tutti"] + sorted(list(set(ruoli_dict.values())))
selected_role = st.sidebar.selectbox("Filtra per Ruolo", ruoli_list)

df_role = df[df["ROLE"] == selected_role] if selected_role != "Tutti" else df

giocatori_list = sorted(df_role["ATHLETE"].unique())
selected_player = st.sidebar.selectbox(
    "Filtra per Giocatore", ["Tutti"] + giocatori_list
)

df_filtered = (
    df_role[df_role["ATHLETE"] == selected_player]
    if selected_player != "Tutti"
    else df_role
)

st.sidebar.divider()
st.sidebar.header("📅 Filtro Temporale")


def extract_week_num(w_str):
  try:
    return int(w_str.replace("Settimana ", ""))
  except Exception:
    return 0


unique_weeks = sorted(
    [w for w in df_filtered["WEEK"].unique() if pd.notna(w)],
    key=extract_week_num,
    reverse=True,
)
settimane_list = ["Tutte le settimane"] + unique_weeks
selected_week = st.sidebar.selectbox("Settimana di Lavoro", settimane_list)

if selected_week != "Tutte le settimane":
  df_filtered = df_filtered[df_filtered["WEEK"] == selected_week]

sessioni_list = ["Tutte le sessioni"] + sorted(
    [d for d in df_filtered["DATE_STR"].unique() if pd.notna(d)], reverse=True
)
selected_session = st.sidebar.selectbox("Data Sessione", sessioni_list)

if selected_session != "Tutte le sessioni":
  df_filtered = df_filtered[df_filtered["DATE_STR"] == selected_session]

# --- ELABORAZIONE DATI ---
daily_summary = (
    df_filtered.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"])
    .agg(
        SALTI_GIORNO=("JUMP HEIGHT(cm)", "count"),
        MAX_GIORNO=("JUMP HEIGHT(cm)", "max"),
        MEDIA_GIORNO=("JUMP HEIGHT(cm)", "mean"),
        IS_MATCH=("IS_MATCH", "max"),
    )
    .reset_index()
)

weekly_summary = (
    df_filtered.groupby(["ATHLETE", "ROLE", "WEEK"])
    .agg(
        SALTI_SETTIMANA=("JUMP HEIGHT(cm)", "count"),
        MAX_SETTIMANA=("JUMP HEIGHT(cm)", "max"),
        MEDIA_SETTIMANA=("JUMP HEIGHT(cm)", "mean"),
    )
    .reset_index()
)

# --- PROFILO GIOCATORE ---
if selected_player != "Tutti":
  role_val = ruoli_dict.get(selected_player, "Atleta")
  details = player_info.get(selected_player, {})
  bio_val = details.get("bio", "Cuneo Volley Prima Squadra")
  link_val = details.get(
      "url", "https://cuneovolley.it/prima-squadra/giocatori"
  )

  st.markdown(
      f"""
    <div class="player-card">
        <div class="player-title">🛡️ {selected_player}</div>
        <div class="player-role">Ruolo: {role_val}</div>
        <p style="color: #475569; margin-top: 8px; margin-bottom: 12px;">{bio_val}</p>
        <a href="{link_val}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 600;">🔗 Vai alla scheda ufficiale Cuneo Volley &rarr;</a>
    </div>
    """,
      unsafe_allow_html=True,
  )

# --- KPI ---
col_g, col_w = st.columns(2)

with col_g:
  st.markdown("##### 📅 Dati Giornalieri (Ultima Sessione)")
  c1, c2, c3 = st.columns(3)
  salti_g = (
      daily_summary["SALTI_GIORNO"].iloc[-1]
      if not daily_summary.empty
      else len(df_filtered)
  )
  max_g = (
      daily_summary["MAX_GIORNO"].max() if not daily_summary.empty else 0
  )
  med_g = (
      daily_summary["MEDIA_GIORNO"].mean() if not daily_summary.empty else 0
  )

  c1.metric("Nr. Salti", f"{salti_g}")
  c2.metric("Salto Max", f"{max_g:.1f} cm")
  c3.metric("Media Salti", f"{med_g:.1f} cm")

with col_w:
  st.markdown("##### 🗓️ Dati Settimanali (Ultima Settimana)")
  c4, c5, c6 = st.columns(3)
  salti_w = (
      weekly_summary["SALTI_SETTIMANA"].iloc[-1]
      if not weekly_summary.empty
      else 0
  )
  max_w = (
      weekly_summary["MAX_SETTIMANA"].max() if not weekly_summary.empty else 0
  )
  med_w = (
      weekly_summary["MEDIA_SETTIMANA"].mean()
      if not weekly_summary.empty
      else 0
  )

  c4.metric("Nr. Salti", f"{salti_w}")
  c5.metric("Salto Max", f"{max_w:.1f} cm")
  c6.metric("Media Salti", f"{med_w:.1f} cm")

st.divider()

# --- GRAFICI DI ANDAMENTO E DISTRIBUZIONE FASCE DI SALTO ---
st.subheader("📈 Grafici di Analisi e Andamento Temporale")

tab_giornaliero, tab_settimanale, tab_fasce = st.tabs(
    [
        "📊 Andamento Giornaliero",
        "🗓️ Andamento Settimanale",
        "🎯 Distribuzione Fasce di Salto",
    ]
)

with tab_giornaliero:
  if not daily_summary.empty:
    chart_df = (
        daily_summary.groupby("DATE_STR")
        .agg(
            SALTI_GIORNO=("SALTI_GIORNO", "sum"),
            MAX_GIORNO=("MAX_GIORNO", "max"),
            MEDIA_GIORNO=("MEDIA_GIORNO", "mean"),
        )
        .reset_index()
        .set_index("DATE_STR")
    )

    st.markdown("##### 🔵 Numero di Salti Giornalieri")
    st.bar_chart(chart_df[["SALTI_GIORNO"]])

    st.markdown("##### 🚀 Salto Max Giornaliero (cm)")
    st.line_chart(chart_df[["MAX_GIORNO"]])

    st.markdown("##### 📊 Media Salti Giornaliera (cm)")
    st.line_chart(chart_df[["MEDIA_GIORNO"]])

with tab_settimanale:
  if not weekly_summary.empty:
    chart_w = (
        weekly_summary.groupby("WEEK")
        .agg(
            SALTI_SETTIMANA=("SALTI_SETTIMANA", "sum"),
            MAX_SETTIMANA=("MAX_SETTIMANA", "max"),
            MEDIA_SETTIMANA=("MEDIA_SETTIMANA", "mean"),
        )
        .reset_index()
        .set_index("WEEK")
    )

    st.markdown("##### 🔵 Numero di Salti Settimanali")
    st.bar_chart(chart_w[["SALTI_SETTIMANA"]])

    st.markdown("##### 🚀 Salto Max Settimanale (cm)")
    st.line_chart(chart_w[["MAX_SETTIMANA"]])

    st.markdown("##### 📊 Media Salti Settimanale (cm)")
    st.line_chart(chart_w[["MEDIA_SETTIMANA"]])

with tab_fasce:
  st.markdown("##### 🎯 Distribuzione Volume Salti per Fasce d'Altezza")
  if not df_filtered.empty:
    # Definizione esplicita dell'ordine desiderato
    order_list = [
        "JUMPS < 30",
        "JUMPS 30-50",
        "JUMPS 50-60",
        "JUMPS 60-70",
        "JUMPS > 70",
    ]

    counts = df_filtered["JUMP_BAND"].value_counts()
    band_df = pd.DataFrame({
        "Fascia": order_list,
        "Numero Salti": [counts.get(b, 0) for b in order_list],
    })

    # Grafico Altair con ordinamento rigido e vincolato
    chart_altair = (
        alt.Chart(band_df)
        .mark_bar(color="#2563eb")
        .encode(
            x=alt.X("Fascia:N", sort=order_list, title="Fascia di Salto"),
            y=alt.Y("Numero Salti:Q", title="Conteggio Salti"),
            tooltip=["Fascia", "Numero Salti"],
        )
        .properties(height=400)
    )

    st.altair_chart(chart_altair, use_container_width=True)
  else:
    st.info("Nessun dato disponibile per i filtri selezionati.")

# --- TABELLE DETTAGLIATE ---
with st.expander("📋 Tabella Dati Completi (Giornaliero e Settimanale)"):
  st.write("**Riepilogo Giornaliero**")
  st.dataframe(daily_summary, use_container_width=True)
  st.write("**Riepilogo Settimanale**")
  st.dataframe(weekly_summary, use_container_width=True)
