import glob
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configurazione della pagina (Sfondo chiaro / Tema pulito)
st.set_page_config(
    page_title="DataJump - Cuneo Volley",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS PERSONALIZZATO CON SFONDO BIANCO E COLORI CUNEO VOLLEY ---
st.markdown(
    """
    <style>
    /* Sfondo generale bianco e testo scuro per massima leggibilità */
    .stApp {
        background-color: #ffffff;
        color: #1f2937;
    }
    
    /* Header Stemma Club */
    .header-container {
        display: flex;
        align-items: center;
        gap: 20px;
        padding-bottom: 12px;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 25px;
    }

    /* Card delle metriche (KPI) su sfondo bianco */
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

    /* Barra laterale (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }

    /* Card Profilo Giocatore */
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

# --- CALENDARIO UFFICIALE MATCH DAY CUNEO VOLLEY (SUPERLEGA 2026/2027) ---
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


# --- CARICAMENTO AUTOMATICO DATI ---
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

# --- PROFILO GIOCATORE / PLAYER CARD UFFICIALE ---
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

# --- VISUALIZZAZIONE KPI ---
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

# --- GRAFICI INTERATTIVI CON EVIDENZA MATCH DAY (COLORE ARANCIONE) ---
st.subheader("📈 Grafici di Andamento Temporale")
st.caption("🟠 I giorni di Match Day sono evidenziati in arancione.")

tab_giornaliero, tab_settimanale = st.tabs(
    ["📊 Andamento Giornaliero per Data", "🗓️ Andamento Settimanale di Lavoro"]
)

with tab_giornaliero:
  if not daily_summary.empty:
    chart_df = (
        daily_summary.groupby("DATE_STR")
        .agg(
            SALTI_GIORNO=("SALTI_GIORNO", "sum"),
            MAX_GIORNO=("MAX_GIORNO", "max"),
            MEDIA_GIORNO=("MEDIA_GIORNO", "mean"),
            IS_MATCH=("IS_MATCH", "max"),
        )
        .reset_index()
    )

    chart_df["TIPO_GIORNO"] = chart_df["IS_MATCH"].apply(
        lambda x: "Match Day 🟠"
        if x
        else "Allenamento / Standard 🔵"
    )
    colore_mappa = {
        "Match Day 🟠": "#f97316",
        "Allenamento / Standard 🔵": "#2563eb",
    }

    # 1. Grafico a barre: Numero di Salti Giornalieri
    st.markdown("##### 🔵 Numero di Salti Giornalieri")
    fig_bar = px.bar(
        chart_df,
        x="DATE_STR",
        y="SALTI_GIORNO",
        color="TIPO_GIORNO",
        color_discrete_map=colore_mappa,
        labels={
            "DATE_STR": "Data Sessione",
            "SALTI_GIORNO": "Nr. Salti",
            "TIPO_GIORNO": "Tipo Sessione",
        },
    )
    fig_bar.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#1f2937",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # 2. Grafico a linee: Salto Max Giornaliero con pallini arancioni sui Match Day
    st.markdown("##### 🚀 Salto Max Giornaliero (cm)")
    fig_line_max = px.line(
        chart_df,
        x="DATE_STR",
        y="MAX_GIORNO",
        markers=True,
        labels={
            "DATE_STR": "Data Sessione",
            "MAX_GIORNO": "Salto Max (cm)",
        },
    )
    fig_line_max.update_traces(
        line=dict(color="#2563eb", width=3),
        marker=dict(
            size=10,
            color=[
                "#f97316" if m else "#2563eb" for m in chart_df["IS_MATCH"]
            ],
        ),
    )
    fig_line_max.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#1f2937",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_line_max, use_container_width=True)

    # 3. Grafico a linee: Media Salti Giornaliera con pallini arancioni sui Match Day
    st.markdown("##### 📊 Media Salti Giornaliera (cm)")
    fig_line_mean = px.line(
        chart_df,
        x="DATE_STR",
        y="MEDIA_GIORNO",
        markers=True,
        labels={
            "DATE_STR": "Data Sessione",
            "MEDIA_GIORNO": "Media Salti (cm)",
        },
    )
    fig_line_mean.update_traces(
        line=dict(color="#2563eb", width=3),
        marker=dict(
            size=10,
            color=[
                "#f97316" if m else "#2563eb" for m in chart_df["IS_MATCH"]
            ],
        ),
    )
    fig_line_mean.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#1f2937",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_line_mean, use_container_width=True)

with tab_settimanale:
  if not weekly_summary.empty:
    chart_w = weekly_summary.groupby("WEEK").agg(
        SALTI_SETTIMANA=("SALTI_SETTIMANA", "sum"),
        MAX_SETTIMANA=("MAX_SETTIMANA", "max"),
        MEDIA_SETTIMANA=("MEDIA_SETTIMANA", "mean"),
    ).reset_index()

    st.markdown("##### 🔵 Numero di Salti Settimanali")
    fig_w_bar = px.bar(
        chart_w,
        x="WEEK",
        y="SALTI_SETTIMANA",
        color_discrete_sequence=["#2563eb"],
    )
    fig_w_bar.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#1f2937",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_w_bar, use_container_width=True)

    st.markdown("##### 🚀 Salto Max Settimanale (cm)")
    fig_w_max = px.line(
        chart_w, x="WEEK", y="MAX_SETTIMANA", markers=True
    )
    fig_w_max.update_traces(
        line=dict(color="#2563eb", width=3), marker=dict(size=10, color="#2563eb")
    )
    fig_w_max.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#1f2937",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_w_max, use_container_width=True)

    st.markdown("##### 📊 Media Salti Settimanale (cm)")
    fig_w_mean = px.line(
        chart_w, x="WEEK", y="MEDIA_SETTIMANA", markers=True
    )
    fig_w_mean.update_traces(
        line=dict(color="#2563eb", width=3), marker=dict(size=10, color="#2563eb")
    )
    fig_w_mean.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#1f2937",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_w_mean, use_container_width=True)

# --- TABELLE DETTAGLIATE ---
with st.expander("📋 Tabella Dati Completi (Giornaliero e Settimanale)"):
  st.write("**Riepilogo Giornaliero**")
  st.dataframe(daily_summary, use_container_width=True)
  st.write("**Riepilogo Settimanale**")
  st.dataframe(weekly_summary, use_container_width=True)
