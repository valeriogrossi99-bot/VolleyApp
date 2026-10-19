import glob
import os
import altair as alt
import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="DataJump",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS PERSONALIZZATO E FORZATURA ICONA PWA NATIVA ---
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
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

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

# --- BARRA LATERALE: FILTRI CONFRONTO MULTIPLO ---
st.sidebar.header("🔍 Filtri Selezione & Confronto")

# Filtro Ruolo
ruoli_list = sorted(list(set(ruoli_dict.values())))
selected_roles = st.sidebar.multiselect("Filtra per Ruolo", ruoli_list)

df_filtered = df.copy()
if selected_roles:
  df_filtered = df_filtered[df_filtered["ROLE"].isin(selected_roles)]

# Filtro Giocatori (permesso confronto multiplo)
giocatori_list = sorted(df_filtered["ATHLETE"].unique())
selected_players = st.sidebar.multiselect(
    "Seleziona Giocatori da Confrontare",
    giocatori_list,
    help="Seleziona uno o più giocatori per confrontarli direttamente",
)

if selected_players:
  df_filtered = df_filtered[df_filtered["ATHLETE"].isin(selected_players)]

st.sidebar.divider()
st.sidebar.header("📅 Filtro Temporale (Sedute & Settimane)")


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
selected_weeks = st.sidebar.multiselect(
    "Seleziona Settimane di Lavoro",
    unique_weeks,
    help="Puoi selezionare più settimane da confrontare",
)

if selected_weeks:
  df_filtered = df_filtered[df_filtered["WEEK"].isin(selected_weeks)]

sessioni_list = sorted(
    [d for d in df_filtered["DATE_STR"].unique() if pd.notna(d)], reverse=True
)
selected_sessions = st.sidebar.multiselect(
    "Seleziona Date/Sedute",
    sessioni_list,
    help="Puoi selezionare più date per confrontare le singole sedute",
)

if selected_sessions:
  df_filtered = df_filtered[df_filtered["DATE_STR"].isin(selected_sessions)]

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

# --- PROFILO GIOCATORE / CARD CONFRONTO ---
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

# --- KPI GENERALE ---
col_g, col_w = st.columns(2)

with col_g:
  st.markdown("##### 📅 Dati Giornalieri (Selezione Corrente)")
  c1, c2, c3 = st.columns(3)
  salti_g = (
      daily_summary["SALTI_GIORNO"].sum()
      if not daily_summary.empty
      else len(df_filtered)
  )
  max_g = (
      daily_summary["MAX_GIORNO"].max() if not daily_summary.empty else 0
  )
  med_g = (
      daily_summary["MEDIA_GIORNO"].mean() if not daily_summary.empty else 0
  )

  c1.metric("Totale Salti", f"{salti_g}")
  c2.metric("Salto Max", f"{max_g:.1f} cm")
  c3.metric("Media Salti", f"{med_g:.1f} cm")

with col_w:
  st.markdown("##### 🗓️ Dati Settimanali (Selezione Corrente)")
  c4, c5, c6 = st.columns(3)
  salti_w = (
      weekly_summary["SALTI_SETTIMANA"].sum()
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

  c4.metric("Totale Salti", f"{salti_w}")
  c5.metric("Salto Max", f"{max_w:.1f} cm")
  c6.metric("Media Salti", f"{med_w:.1f} cm")

st.divider()

# --- GRAFICI DI ANDAMENTO, CONFRONTI E DISTRIBUZIONE ---
st.subheader("📈 Grafici di Analisi & Confronti")

tab_giornaliero, tab_settimanale, tab_confronto, tab_fasce = st.tabs([
    "📊 Andamento Giornaliero",
    "🗓️ Andamento Settimanale",
    "⚔️ Confronto Diretto Giocatori",
    "🎯 Distribuzione Fasce di Salto",
])

with tab_giornaliero:
  if not daily_summary.empty:
    st.markdown("##### 🔵 Numero di Salti per Data e Giocatore")
    chart_bar = (
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
    st.altair_chart(chart_bar, use_container_width=True)

    st.markdown("##### 🚀 Salto Max Giornaliero (cm)")
    chart_line_max = (
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
    st.altair_chart(chart_line_max, use_container_width=True)

with tab_settimanale:
  if not weekly_summary.empty:
    st.markdown("##### 🔵 Numero di Salti Settimanali per Giocatore")
    chart_w_bar = (
        alt.Chart(weekly_summary)
        .mark_bar()
        .encode(
            x=alt.X("WEEK:N", title="Settimana"),
            y=alt.Y("SALTI_SETTIMANA:Q", title="Nr. Salti"),
            color=alt.Color("ATHLETE:N", title="Giocatore"),
            tooltip=["WEEK", "ATHLETE", "SALTI_SETTIMANA", "MAX_SETTIMANA"],
        )
        .properties(height=380)
    )
    st.altair_chart(chart_w_bar, use_container_width=True)

    st.markdown("##### 🚀 Salto Max Settimanale (cm)")
    chart_w_line = (
        alt.Chart(weekly_summary)
        .mark_line(point=True)
        .encode(
            x=alt.X("WEEK:N", title="Settimana"),
            y=alt.Y("MAX_SETTIMANA:Q", title="Salto Max (cm)"),
            color=alt.Color("ATHLETE:N", title="Giocatore"),
            tooltip=["WEEK", "ATHLETE", "MAX_SETTIMANA"],
        )
        .properties(height=380)
    )
    st.altair_chart(chart_w_line, use_container_width=True)

with tab_confronto:
  st.markdown("##### ⚔️ Confronto Totale Volume & Max tra Giocatori")
  if not df_filtered.empty:
    comp_df = (
        df_filtered.groupby(["ATHLETE", "ROLE"])
        .agg(
            TOT_SALTI=("JUMP HEIGHT(cm)", "count"),
            MAX_SALTO=("JUMP HEIGHT(cm)", "max"),
            MEDIA_SALTO=("JUMP HEIGHT(cm)", "mean"),
        )
        .reset_index()
    )

    col_comp1, col_comp2 = st.columns(2)

    with col_comp1:
      st.write("**Totale Salti per Giocatore**")
      chart_comp_salti = (
          alt.Chart(comp_df)
          .mark_bar(color="#2563eb")
          .encode(
              x=alt.X("ATHLETE:N", title="Giocatore", sort="-y"),
              y=alt.Y("TOT_SALTI:Q", title="Totale Salti"),
              tooltip=["ATHLETE", "ROLE", "TOT_SALTI"],
          )
          .properties(height=350)
      )
      st.altair_chart(chart_comp_salti, use_container_width=True)

    with col_comp2:
      st.write("**Salto Massimo (cm) per Giocatore**")
      chart_comp_max = (
          alt.Chart(comp_df)
          .mark_bar(color="#f97316")
          .encode(
              x=alt.X("ATHLETE:N", title="Giocatore", sort="-y"),
              y=alt.Y("MAX_SALTO:Q", title="Salto Max (cm)"),
              tooltip=["ATHLETE", "ROLE", "MAX_SALTO"],
          )
          .properties(height=350)
      )
      st.altair_chart(chart_comp_max, use_container_width=True)

    st.write("**Tabella Sintetica di Confronto**")
    st.dataframe(comp_df, use_container_width=True)
  else:
    st.info("Seleziona almeno un giocatore per visualizzare il confronto.")

with tab_fasce:
  st.markdown("##### 🎯 Distribuzione Volume Salti per Fasce d'Altezza")
  if not df_filtered.empty:
    order_list = [
        "JUMPS < 30",
        "JUMPS 30-50",
        "JUMPS 50-60",
        "JUMPS 60-70",
        "JUMPS > 70",
    ]

    band_comp = (
        df_filtered.groupby(["JUMP_BAND", "ATHLETE"])
        .size()
        .reset_index(name="Numero Salti")
    )

    chart_altair = (
        alt.Chart(band_comp)
        .mark_bar()
        .encode(
            x=alt.X("JUMP_BAND:N", sort=order_list, title="Fascia di Salto"),
            y=alt.Y("Numero Salti:Q", title="Conteggio Salti"),
            color=alt.Color("ATHLETE:N", title="Giocatore"),
            tooltip=["JUMP_BAND", "ATHLETE", "Numero Salti"],
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
