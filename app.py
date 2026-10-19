import glob
import os
import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Volley Performance App", page_icon="🏐", layout="wide"
)

st.title("🏐 Volley Performance Dashboard - Analytics Salti")

# --- ROSTER UFFICIALE E RUOLI ---
ruoli_dict = {
    # Palleggiatori
    "Bryan Argilagos": "Palleggiatore",
    "Manuel Coscione": "Palleggiatore",
    # Schiacciatori
    "Alexandre Strehlau": "Schiacciatore",
    "Ethan Champlin": "Schiacciatore",
    "Federico Giraudo": "Schiacciatore",
    "Poriya Khanzadeh": "Schiacciatore",
    # Opposti
    "Nathan Feral": "Opposto",
    "Lorenzo Sala": "Opposto",
    # Centrali
    "Emanuele Barberio": "Centrale",
    "Leandro Mosca": "Centrale",
    "Lorenzo Codarin": "Centrale",
    "Nicoló Volpe": "Centrale",
}


# --- CARICAMENTO AUTOMATICO DI TUTTI I FILE CSV ---
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

  # Nome atleta e associazione ruolo
  df["ATHLETE"] = (
      df["NAME"].astype(str).str.strip()
      + " "
      + df["SURNAME"].astype(str).str.strip()
  )
  df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")

  # Gestione date e settimane ISO
  df["DATE_DT"] = pd.to_datetime(df["DATE"], errors="coerce")
  df["DATE_STR"] = df["DATE_DT"].dt.strftime("%Y-%m-%d")

  iso_cal = df["DATE_DT"].dt.isocalendar()
  df["WEEK"] = (
      iso_cal["year"].astype(str)
      + "-W"
      + iso_cal["week"].astype(str).str.zfill(2)
  )

  return df


df = load_all_sessions()

if df.empty:
  st.warning(
      "⚠️ Nessun file CSV valido trovato. Carica i file CSV nella cartella"
      " 'data/' o nella radice del progetto."
  )
  st.stop()

# --- BARRA LATERALE: FILTRI ---
st.sidebar.header("🔍 Filtri Selezione")

# 1. Filtro Ruolo
ruoli_list = ["Tutti"] + sorted(list(set(ruoli_dict.values())))
selected_role = st.sidebar.selectbox("Filtra per Ruolo", ruoli_list)

if selected_role != "Tutti":
  df_role = df[df["ROLE"] == selected_role]
else:
  df_role = df

# 2. Filtro Giocatore
giocatori_list = sorted(df_role["ATHLETE"].unique())
selected_player = st.sidebar.selectbox(
    "Filtra per Giocatore", ["Tutti"] + giocatori_list
)

if selected_player != "Tutti":
  df_filtered = df_role[df_role["ATHLETE"] == selected_player]
else:
  df_filtered = df_role

# 3. Filtri Temporali
st.sidebar.divider()
st.sidebar.header("📅 Filtro Temporale")

settimane_list = ["Tutte le settimane"] + sorted(
    [w for w in df_filtered["WEEK"].unique() if pd.notna(w)], reverse=True
)
selected_week = st.sidebar.selectbox("Settimana ISO", settimane_list)

if selected_week != "Tutte le settimane":
  df_filtered = df_filtered[df_filtered["WEEK"] == selected_week]

sessioni_list = ["Tutte le sessioni"] + sorted(
    [d for d in df_filtered["DATE_STR"].unique() if pd.notna(d)], reverse=True
)
selected_session = st.sidebar.selectbox("Data Sessione", sessioni_list)

if selected_session != "Tutte le sessioni":
  df_filtered = df_filtered[df_filtered["DATE_STR"] == selected_session]


# --- ELABORAZIONE DATI GIORNALIERI E SETTIMANALI ---
# A) Raggruppamento Giornaliero (Sessione)
daily_summary = (
    df_filtered.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"])
    .agg(
        SALTI_GIORNO=("JUMP HEIGHT(cm)", "count"),
        MAX_GIORNO=("JUMP HEIGHT(cm)", "max"),
        MEDIA_GIORNO=("JUMP HEIGHT(cm)", "mean"),
    )
    .reset_index()
)

# B) Raggruppamento Settimanale
weekly_summary = (
    df_filtered.groupby(["ATHLETE", "ROLE", "WEEK"])
    .agg(
        SALTI_SETTIMANA=("JUMP HEIGHT(cm)", "count"),
        MAX_SETTIMANA=("JUMP HEIGHT(cm)", "max"),
        MEDIA_SETTIMANA=("JUMP HEIGHT(cm)", "mean"),
    )
    .reset_index()
)

# --- VISUALIZZAZIONE PANNELLI KPI ---
st.subheader(
    f"📊 Riepilogo Prestazioni - Giocatore: {selected_player} | Ruolo:"
    f" {selected_role}"
)

# SEZIONE GIORNALIERA (SESSIONE)
st.markdown("### 📅 Dati Giornalieri (Ultima Sessione Selezionata)")
col1, col2, col3 = st.columns(3)

with col1:
  salti_g = (
      daily_summary["SALTI_GIORNO"].iloc[-1]
      if not daily_summary.empty
      else len(df_filtered)
  )
  st.metric("Nr. Salti (Giornaliero)", f"{salti_g}")
with col2:
  max_g = (
      daily_summary["MAX_GIORNO"].max() if not daily_summary.empty else 0
  )
  st.metric("Salto Max (Giornaliero)", f"{max_g:.1f} cm")
with col3:
  med_g = (
      daily_summary["MEDIA_GIORNO"].mean() if not daily_summary.empty else 0
  )
  st.metric("Media Salti (Giornaliera)", f"{med_g:.1f} cm")

st.divider()

# SEZIONE SETTIMANALE
st.markdown("### 🗓️ Dati Settimanali (Ultima Settimana Selezionata)")
col4, col5, col6 = st.columns(3)

with col4:
  salti_w = (
      weekly_summary["SALTI_SETTIMANA"].iloc[-1]
      if not weekly_summary.empty
      else 0
  )
  st.metric("Nr. Salti (Settimanale)", f"{salti_w}")
with col5:
  max_w = (
      weekly_summary["MAX_SETTIMANA"].max() if not weekly_summary.empty else 0
  )
  st.metric("Salto Max (Settimanale)", f"{max_w:.1f} cm")
with col6:
  med_w = (
      weekly_summary["MEDIA_SETTIMANA"].mean()
      if not weekly_summary.empty
      else 0
  )
  st.metric("Media Salti (Settimanale)", f"{med_w:.1f} cm")

st.divider()

# --- GRAFICI DI ANDAMENTO TEMPORALE GIORNALIERO E SETTIMANALE ---
st.subheader("📈 Grafici di Andamento Temporale")

tab_giornaliero, tab_settimanale = st.tabs(
    ["📊 Andamento Giornaliero per Data", "🗓️ Andamento Settimanale per Settimana"]
)

with tab_giornaliero:
  col_g1, col_g2, col_g3 = st.columns(3)

  with col_g1:
    st.write("**Numero di Salti Giornalieri**")
    if not daily_summary.empty:
      chart_salti_g = daily_summary.pivot_table(
          index="DATE_STR", values="SALTI_GIORNO", aggfunc="sum"
      )
      st.bar_chart(chart_salti_g)

  with col_g2:
    st.write("**Salto Max Giornaliero (cm)**")
    if not daily_summary.empty:
      chart_max_g = daily_summary.pivot_table(
          index="DATE_STR", values="MAX_GIORNO", aggfunc="max"
      )
      st.line_chart(chart_max_g)

  with col_g3:
    st.write("**Media Salti Giornaliera (cm)**")
    if not daily_summary.empty:
      chart_med_g = daily_summary.pivot_table(
          index="DATE_STR", values="MEDIA_GIORNO", aggfunc="mean"
      )
      st.line_chart(chart_med_g)

with tab_settimanale:
  col_w1, col_w2, col_w3 = st.columns(3
