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


# --- CARICAMENTO AUTOMATICO DI TUTTI I FILE DA GITHUB ---
@st.cache_data
def load_all_sessions():
  # Cerca sia nella cartella data/ che nella radice del progetto
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

  # Pulizia spazi nei nomi delle colonne se presenti
  df.columns = df.columns.str.strip()

  # Creazione atleta e ruolo
  df["ATHLETE"] = (
      df["NAME"].astype(str).str.strip()
      + " "
      + df["SURNAME"].astype(str).str.strip()
  )
  df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")

  # Conversione Data e Settimana ISO in modo sicuro
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
      "⚠️ Nessun file CSV valido trovato. Verifica di aver caricato il file dei"
      " salti su GitHub."
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

# 3. Filtro Settimana / Sessione
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


# --- CALCOLO METRICHE AVANZATE PER SESSIONE ---
def calculate_session_metrics(data):
  if data.empty:
    return pd.DataFrame()

  grouped = data.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"])

  # Calcolo dei 5 migliori salti per sessione (AVG Top 5)
  top5_avg = (
      data.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"])["JUMP HEIGHT(cm)"]
      .nlargest(5)
      .groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"])
      .mean()
      .reset_index(name="AVG_TOP_5")
  )

  metrics = grouped.agg(
      SALTI_SESSIONE=("JUMP HEIGHT(cm)", "count"),
      MAX_JUMP=("JUMP HEIGHT(cm)", "max"),
      AVG_JUMP=("JUMP HEIGHT(cm)", "mean"),
      AVG_IMPACT=("LANDING IMPACT (g)", "mean"),
  ).reset_index()

  res = pd.merge(metrics, top5_avg, on=["ATHLETE", "ROLE", "DATE_STR", "WEEK"])
  return res


session_summary = calculate_session_metrics(df_filtered)

# --- PANNELLO METRICHE CHIAVE ---
st.subheader(
    f"📊 Summary Metriche - Giocatore: {selected_player} | Ruolo:"
    f" {selected_role}"
)

col1, col2, col3, col4, col5 = st.columns(5)

tot_salti_settimana = df_filtered.groupby("WEEK")["JUMP HEIGHT(cm)"].count()
val_salti_sett = (
    tot_salti_settimana.iloc[-1]
    if not tot_salti_settimana.empty
    else len(df_filtered)
)

with col1:
  st.metric("Salti Totali (Filtro)", len(df_filtered))
with col2:
  salti_sess = (
      session_summary["SALTI_SESSIONE"].mean()
      if not session_summary.empty
      else 0
  )
  st.metric("Media Salti / Sessione", f"{salti_sess:.0f}")
with col3:
  max_salto = (
      session_summary["MAX_JUMP"].max() if not session_summary.empty else 0
  )
  st.metric("Salto Max Assoluto", f"{max_salto:.1f} cm")
with col4:
  avg_top5 = (
      session_summary["AVG_TOP_5"].max() if not session_summary.empty else 0
  )
  st.metric("Top AVG 5 Best Jump", f"{avg_top5:.1f} cm")
with col5:
  imp_med = (
      session_summary["AVG_IMPACT"].mean() if not session_summary.empty else 0
  )
  st.metric("Impatto Medio Atterraggio", f"{imp_med:.1f} g")

st.divider()

# --- GRAFICI DI ANDAMENTO TEMPORALE ---
st.subheader("📈 Grafici di Andamento Temporale per Sessione")

tab1, tab2, tab3 = st.tabs([
    "🚀 Salto Max & AVG Top 5",
    "🔄 Volume Salti (Sessione)",
    "⚡ Impatto Atterraggio (g)",
])

with tab1:
  st.write("##### Andamento Salto Max e Media dei 5 Migliori Salti (cm)")
  if not session_summary.empty:
    chart_data = session_summary.pivot_table(
        index="DATE_STR", values=["MAX_JUMP", "AVG_TOP_5"], aggfunc="max"
    )
    st.line_chart(chart_data)
  else:
    st.info("Nessun dato disponibile con i filtri attuali.")

with tab2:
  st.write("##### Volume Salti per Sessione")
  if not session_summary.empty:
    chart_sess = session_summary.pivot_table(
        index="DATE_STR", values="SALTI_SESSIONE", aggfunc="sum"
    )
    st.bar_chart(chart_sess)
  else:
    st.info("Nessun dato disponibile.")

with tab3:
  st.write("##### Andamento dell'Impatto all'Atterraggio (g)")
  if not session_summary.empty:
    chart_impact = session_summary.pivot_table(
        index="DATE_STR", values="AVG_IMPACT", aggfunc="mean"
    )
    st.line_chart(chart_impact)
  else:
    st.info("Nessun dato disponibile.")

# --- REGISTRO DETTAGLIATO PER SESSIONE ---
with st.expander("📋 Tabella Riassuntiva per Sessione"):
  st.dataframe(session_summary)
