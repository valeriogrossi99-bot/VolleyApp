import pandas as pd
import streamlit as st

# Impostazione della pagina web
st.set_page_config(
    page_title="Volley Performance App", page_icon="🏐", layout="wide"
)

st.title("🏐 Volley Performance Dashboard")


# Caricamento dei dati dal CSV
@st.cache_data
def load_data():
  # Il nome del file deve corrispondere esattamente al file caricato su GitHub
  filename = "PERFBOOK_JUMPS_Total Area_2026_10_15_17_53_44.csv"
  df = pd.read_csv(filename, sep=";")
  df["ATHLETE"] = df["NAME"] + " " + df["SURNAME"]
  return df


# Tenta il caricamento, se il file non c'è mostra un messaggio di errore chiaro
try:
  df = load_data()
except Exception as e:
  st.error(
      f"⚠️ Impossibile trovare o leggere il file CSV dei salti. Assicurati che"
      f" il file sia caricato su GitHub. Dettagli errore: {e}"
  )
  st.stop()

# Tabella Ruoli per filtro
# --- ROSTER UFFICIALE E RUOLI ---
ruoli_dict = {
    # Palleggiatori (P)
    "Bryan Argilagos": "Palleggiatore",
    "Manuel Coscione": "Palleggiatore",
    # Schiacciatori (S)
    "Alexandre Strehlau": "Schiacciatore",
    "Ethan Champlin": "Schiacciatore",
    "Federico Giraudo": "Schiacciatore",
    "Poriya Khanzadeh": "Schiacciatore",
    # Opposti (O)
    "Nathan Feral": "Opposto",
    "Lorenzo Sala": "Opposto",
    # Centrali (C)
    "Emanuele Barberio": "Centrale",
    "Leandro Mosca": "Centrale",
    "Lorenzo Codarin": "Centrale",
    "Nicoló Volpe": "Centrale",
    # Liberi (L)
    "Mimmo Cavaccini": "Libero",
    "Thibault Loubeyre": "Libero",
}

df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Non Assegnato")

# BARRA LATERALE PER I FILTRI
st.sidebar.header("🔍 Filtri")

# Filtro Ruolo
selected_role = st.sidebar.selectbox(
    "Ruolo", ["Tutti"] + sorted(list(set(ruoli_dict.values())))
)
if selected_role != "Tutti":
  df_filtered = df[df["ROLE"] == selected_role]
else:
  df_filtered = df

# Filtro Giocatore
selected_player = st.sidebar.selectbox(
    "Giocatore", ["Tutti"] + sorted(df_filtered["ATHLETE"].unique())
)
if selected_player != "Tutti":
  df_filtered = df_filtered[df_filtered["ATHLETE"] == selected_player]

# METRICHE E KPI
st.subheader("📊 Metriche Principali")
col1, col2, col3, col4 = st.columns(4)

with col1:
  st.metric("Salti Totali", len(df_filtered))
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
  st.metric("Impatto Medio", f"{mean_impact:.1f} g")

st.divider()

# GRAFICI
st.subheader("📈 Andamento e Analisi dei Salti")
col_a, col_b = st.columns(2)

with col_a:
  st.write("**Altezza dei Salti (Sequenza Temporale)**")
  if not df_filtered.empty:
    st.line_chart(df_filtered["JUMP HEIGHT(cm)"].reset_index(drop=True))

with col_b:
  st.write("**Altezza vs Impatto Atterraggio**")
  if not df_filtered.empty:
    st.scatter_chart(
        df_filtered, x="JUMP HEIGHT(cm)", y="LANDING IMPACT (g)"
    )

# TABELLA DATI
with st.expander("📋 Mostra Dati Dettagliati"):
  st.dataframe(df_filtered)
