import glob
import os
import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Volley Performance App",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS PERSONALIZZATO PER GRAFICA E PLAYER CARD ---
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background-color: #1E222D;
        border: 1px solid #2A2E3D;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetric"] label {
        color: #8B949E !important;
        font-size: 0.9rem !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #58A6FF !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🏐 Volley Performance Dashboard")
st.caption("Monitoraggio carichi e analisi dinamica dei salti - Sola Lettura")

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

# (Facoltativo) Link di riferimento o immagini ufficiali dei giocatori
# Puoi inserire qui i link diretti alle foto o ai profili
player_info = {
    "Bryan Argilagos": {
        "maglia": "#",
        "bio": "Palleggiatore - Classe 2007",
    },
    "Manuel Coscione": {"maglia": "#", "bio": "Palleggiatore - Classe 1980"},
    "Alexandre Strehlau": {"maglia": "#", "bio": "Schiacciatore - Classe 2004"},
    "Ethan Champlin": {"maglia": "#", "bio": "Schiacciatore - Classe 2001"},
    "Federico Giraudo": {"maglia": "#", "bio": "Schiacciatore - Classe 2007"},
    "Poriya Khanzadeh": {"maglia": "#", "bio": "Schiacciatore - Classe 2004"},
    "Nathan Feral": {"maglia": "#", "bio": "Opposto - Classe 2003"},
    "Lorenzo Sala": {"maglia": "#", "bio": "Opposto - Classe 2002"},
    "Emanuele Barberio": {"maglia": "#", "bio": "Centrale - Classe 2007"},
    "Leandro Mosca": {"maglia": "#", "bio": "Centrale - Classe 2000"},
    "Lorenzo Codarin": {"maglia": "#", "bio": "Centrale - Classe 1996"},
    "Nicoló Volpe": {"maglia": "#", "bio": "Centrale - Classe 2003"},
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

# --- PROFILO GIOCATORE / PLAYER CARD ---
if selected_player != "Tutti":
  role_val = ruoli_dict.get(selected_player, "Atleta")
  info_val = player_info.get(selected_player, {}).get("bio", "Cuneo Volley")

  col_avatar, col_info = st.columns([1, 4])
  with col_avatar:
    # Mostra un'icona o immagine placeholder personalizzabile
    st.image(
        "https://img.icons8.com/color/96/volleyball.png",
        width=100,
    )
  with col_info:
    st.markdown(f"### 👤 {selected_player}")
    st.markdown(f"**Ruolo:** `{role_val}` | **Dettagli:** {info_val}")
    st.markdown(
        "🔗 [Visulaizza la scheda ufficiale su Cuneo"
        " Volley](https://cuneovolley.it/prima-squadra/giocatori)"
    )
  st.divider()

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

# --- GRAFICI ---
st.subheader("📈 Grafici di Andamento Temporale")

tab_giornaliero, tab_settimanale = st.tabs(
    ["📊 Andamento Giornaliero per Data", "🗓️ Andamento Settimanale di Lavoro"]
)

with tab_giornaliero:
  col_g1, col_g2, col_g3 = st.columns(3)
  with col_g1:
    st.write("**Numero di Salti Giornalieri**")
    if not daily_summary.empty:
      st.bar_chart(
          daily_summary.pivot_table(
              index="DATE_STR", values="SALTI_GIORNO", aggfunc="sum"
          )
      )
  with col_g2:
    st.write("**Salto Max Giornaliero (cm)**")
    if not daily_summary.empty:
      st.line_chart(
          daily_summary.pivot_table(
              index="DATE_STR", values="MAX_GIORNO", aggfunc="max"
          )
      )
  with col_g3:
    st.write("**Media Salti Giornaliera (cm)**")
    if not daily_summary.empty:
      st.line_chart(
          daily_summary.pivot_table(
              index="DATE_STR", values="MEDIA_GIORNO", aggfunc="mean"
          )
      )

with tab_settimanale:
  col_w1, col_w2, col_w3 = st.columns(3)
  with col_w1:
    st.write("**Numero di Salti Settimanali**")
    if not weekly_summary.empty:
      st.bar_chart(
          weekly_summary.pivot_table(
              index="WEEK", values="SALTI_SETTIMANA", aggfunc="sum"
          )
      )
  with col_w2:
    st.write("**Salto Max Settimanale (cm)**")
    if not weekly_summary.empty:
      st.line_chart(
          weekly_summary.pivot_table(
              index="WEEK", values="MAX_SETTIMANA", aggfunc="max"
          )
      )
  with col_w3:
    st.write("**Media Salti Settimanale (cm)**")
    if not weekly_summary.empty:
      st.line_chart(
          weekly_summary.pivot_table(
              index="WEEK", values="MEDIA_SETTIMANA", aggfunc="mean"
          )
      )

# --- TABELLE DETTAGLIATE ---
with st.expander("📋 Tabella Dati Completi (Giornaliero e Settimanale)"):
  st.write("**Riepilogo Giornaliero**")
  st.dataframe(daily_summary, use_container_width=True)
  st.write("**Riepilogo Settimanale**")
  st.dataframe(weekly_summary, use_container_width=True)
