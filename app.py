import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(
    page_title="Volley Performance App", page_icon="🏐", layout="wide"
)

st.title("🏐 Volley Performance Dashboard")

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

# --- BARRA LATERALE: UPLOAD FILE MULTIPLI ---
st.sidebar.header("📁 Carica Sedute (CSV)")

uploaded_files = st.sidebar.file_uploader(
    "Seleziona uno o più file CSV di PerfBook",
    type=["csv"],
    accept_multiple_files=True,
)

lista_dataframe = []

# 1. Se l'utente carica dei file dall'interfaccia dell'app
if uploaded_files:
  for file in uploaded_files:
    try:
      df_temp = pd.read_csv(file, sep=";")
      lista_dataframe.append(df_temp)
    except Exception as e:
      st.sidebar.error(f"Errore nel caricare {file.name}: {e}")

# 2. Se non sono caricati file manualmente, proviamo a caricare il file di default su GitHub
else:
  filename_default = "PERFBOOK_JUMPS_Total Area_2026_10_15_17_53_44.csv"
  try:
    df_default = pd.read_csv(filename_default, sep=";")
    lista_dataframe.append(df_default)
  except Exception:
    pass

# Se nessun file è presente o caricato
if not lista_dataframe:
  st.warning(
      "⚠️ Nessun file dati caricato. Utilizza la barra laterale per caricare i"
      " file CSV delle sedute."
  )
  st.stop()

# Unione di tutti i file CSV in un unico grande DataFrame
df_totale = pd.concat(lista_dataframe, ignore_index=True)

# Creazione colonna Nome Completo
df_totale["ATHLETE"] = df_totale["NAME"] + " " + df_totale["SURNAME"]

# Assegnazione Ruolo
df_totale["ROLE"] = df_totale["ATHLETE"].map(ruoli_dict).fillna("Non Assegnato")

# Pulizia/Conversione della colonna Data se presente
if "DATE" in df_totale.columns:
  df_totale["DATE"] = pd.to_datetime(df_totale["DATE"]).dt.strftime("%Y-%m-%d")

# --- BARRA LATERALE: FILTRI ---
st.sidebar.divider()
st.sidebar.header("🔍 Filtri")

# Filtro Ruolo
ruoli_disponibili = ["Tutti"] + sorted(list(set(ruoli_dict.values())))
selected_role = st.sidebar.selectbox("Filtra per Ruolo", ruoli_disponibili)

if selected_role != "Tutti":
  df_filtered = df_totale[df_totale["ROLE"] == selected_role]
else:
  df_filtered = df_totale

# Filtro Giocatore
giocatori_disponibili = ["Tutti"] + sorted(df_filtered["ATHLETE"].unique())
selected_player = st.sidebar.selectbox(
    "Filtra per Giocatore", giocatori_disponibili
)

if selected_player != "Tutti":
  df_filtered = df_filtered[df_filtered["ATHLETE"] == selected_player]

# Filtro Data (se presenti più sedute)
if "DATE" in df_filtered.columns:
  date_disponibili = ["Tutte le date"] + sorted(
      df_filtered["DATE"].unique().tolist()
  )
  selected_date = st.sidebar.selectbox(
      "Filtra per Data Seduta", date_disponibili
  )
  if selected_date != "Tutte le date":
    df_filtered = df_filtered[df_filtered["DATE"] == selected_date]

# --- METRICHE E KPI ---
st.subheader("📊 Metriche Principali")
col1, col2, col3, col4 = st.columns(4)

with col1:
  st.metric("Salti Totali Registrati", len(df_filtered))
with col2:
  max_h = (
      df_filtered["JUMP HEIGHT(cm)"].max() if not df_filtered.empty else 0
  )
  st.metric("Altezza Max", f"{max_h:.1f} cm")
with col3:
  mean_h = (
      df_filtered["JUMP HEIGHT(cm)"].mean() if not df_filtered.empty else 0
  )
  st.metric("Altezza Media", f"{mean_h:.1f} cm")
with col4:
  mean_impact = (
      df_filtered["LANDING IMPACT (g)"].mean() if not df_filtered.empty else 0
  )
  st.metric("Impatto Medio Atterraggio", f"{mean_impact:.1f} g")

st.divider()

# --- GRAFICI ---
st.subheader("📈 Analisi dei Salti")
col_a, col_b = st.columns(2)

with col_a:
  st.write("**Andamento Altezza Salti**")
  if not df_filtered.empty:
    st.line_chart(df_filtered["JUMP HEIGHT(cm)"].reset_index(drop=True))
  else:
    st.info("Nessun dato con i filtri attuali.")

with col_b:
  st.write("**Rapporto Altezza Salto vs Impatto (g)**")
  if not df_filtered.empty:
    st.scatter_chart(
        df_filtered, x="JUMP HEIGHT(cm)", y="LANDING IMPACT (g)"
    )
  else:
    st.info("Nessun dato con i filtri attuali.")

# TABELLA DATI
with st.expander("📋 Mostra Registro Dati"):
  st.dataframe(df_filtered)
