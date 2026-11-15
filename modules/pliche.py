import streamlit as st
import pandas as pd
import altair as alt
import requests
import io
import urllib.parse

# ID del Google Sheet delle pliche fornito da te
PLICHE_SHEET_ID = "1zH8w4hePJK531fxq0RGGX7az76EEz4c7vXWF5tCM1mc"

@st.cache_data(ttl=60)
def load_pliche_data():
    """Scarica e unisce tutte le schede (date di controllo) dal Google Sheet delle pliche."""
    # Prima scarichiamo il file in formato xlsx per leggere l'elenco di tutte le schede (fogli)
    url_xlsx = f"https://docs.google.com/spreadsheets/d/{PLICHE_SHEET_ID}/export?format=xlsx"
    try:
        r = requests.get(url_xlsx, timeout=30)
        if r.status_code != 200:
            return pd.DataFrame()
        
        book = pd.read_excel(io.BytesIO(r.content), sheet_name=None, header=None)
    except Exception:
        return pd.DataFrame()
    
    all_rows = []
    
    for sheet_name, df in book.items():
        # Saltiamo la scheda 'Info' o schede di servizio se presenti
        if str(sheet_name).strip().lower() == 'info':
            continue
            
        data_controllo = str(sheet_name).strip()
        
        # Cerchiamo la riga che contiene la intestazione "Giocatore" o "Atleta"
        header_row_idx = None
        for i in range(min(len(df), 10)):
            row_vals = [str(val).strip().lower() for val in df.iloc[i].values]
            if any("giocatore" in val or "atleta" in val for val in row_vals):
                header_row_idx = i
                break
        
        if header_row_idx is None:
            continue
            
        # Impostiamo la riga corretta come intestazione per questa scheda
        sub_df = df.iloc[header_row_idx:].copy()
        sub_df.columns = sub_df.iloc[0]
        sub_df = sub_df.iloc[1:].reset_index(drop=True)
        
        # Pulizia nomi colonne (rimuoviamo spazi vuoti o NaN)
        sub_df = sub_df.loc[:, sub_df.columns.notna()]
        sub_df.columns = [str(c).strip() for c in sub_df.columns]
        
        # Identifichiamo la colonna dei nomi/etichette di riga (es. "Peso (Kg)", "Sottoscapolare", ecc.)
        label_col = sub_df.columns[0]
        
        # Trasponiamo o analizziamo le colonne dei giocatori
        # Ogni colonna successiva alla prima corrisponde a un giocatore
        player_cols = sub_df.columns[1:]
        
        for col in player_cols:
            player_name = str(col).strip()
            if not player_name or player_name.lower() == 'nan':
                continue
                
            # Estraiamo i valori per questo giocatore in questa data
            p_data = {"Atleta": player_name, "DataControllo": data_controllo}
            
            for idx, row in sub_df.iterrows():
                metric_name = str(row[label_col]).strip()
                if not metric_name or metric_name.lower() == 'nan':
                    continue
                val = row[col]
                # Tentiamo di convertire in numero se possibile
                try:
                    val_num = float(str(val).replace(',', '.').strip())
                except Exception:
                    val_num = val  # Lasciamo stringa se è un testo
                
                p_data[metric_name] = val_num
                
            all_rows.append(p_data)
            
    if not all_rows:
        return pd.DataFrame()
        
    df_result = pd.DataFrame(all_rows)
    return df_result


def render(allowed_athletes, ruoli_dict):
    st.markdown("### 📏 **Pliche Cutanee & Composizione Corporea**")
    
    if allowed_athletes == "ALL":
        st.success("🔓 Visualizzazione: Roster Completo")
    else:
        st.success(f"🔓 Visualizzazione Dedicata: {allowed_athletes[0]}")
        
    with st.spinner("Caricamento dati antropometrici da Google Drive..."):
        df_pliche = load_pliche_data()
        
    if df_pliche.empty:
        st.warning("⚠️ Impossibile leggere i dati dal foglio delle pliche o il formato non è riconosciuto.")
        if st.button("🏠 Torna alla Home"):
            st.session_state.page = "home"
            st.rerun()
        return

    # Normalizzazione nomi atleti rispetto al dizionario globale
    if "Atleta" in df_pliche.columns:
        df_pliche["ATHLETE"] = df_pliche["Atleta"].astype(str).str.strip()
    else:
        st.warning("⚠️ Colonna 'Atleta' non trovata nel foglio.")
        return

    if allowed_athletes != "ALL":
        df_pliche = df_pliche[df_pliche["ATHLETE"].isin(allowed_athletes)]

    # Filtri laterali
    st.sidebar.divider()
    st.sidebar.header("🔍 Filtri Pliche")
    giocatori_list = sorted(df_pliche["ATHLETE"].unique())
    selected_player = st.sidebar.selectbox("Seleziona Giocatore", giocatori_list)

    df_player = df_pliche[df_pliche["ATHLETE"] == selected_player]

    st.markdown(f"#### 👤 Atleta: **{selected_player}**")

    # Mostriamo una tabella riepilogativa con tutte le date di controllo e le metriche principali (Peso, Totale pliche, Media pliche)
    st.markdown("##### 📋 Storico Controlli Antropometrici")
    
    # Identifichiamo le colonne chiave presenti nel dataframe
    cols_presenti = [c for c in df_player.columns if c not in ["Atleta", "ATHLETE"]]
    
    if not df_player.empty:
        st.dataframe(df_player[cols_presenti], use_container_width=True, hide_index=True)
        
        # Grafico dell'andamento del Peso se la colonna esiste
        peso_col_candidates = [c for c in df_player.columns if "peso" in c.lower()]
        if peso_col_candidates:
            p_col = peso_col_candidates[0]
            st.markdown("##### ⚖️ Andamento Peso (Kg)")
            chart_peso = alt.Chart(df_player).mark_line(point=True, strokeWidth=3, color="#2563eb").encode(
                x=alt.X("DataControllo:N", title="Controllo / Data", sort=None),
                y=alt.Y(f"{p_col}:Q", title="Peso (Kg)", scale=alt.Scale(zero=False)),
                tooltip=["DataControllo", alt.Tooltip(f"{p_col}:Q", title="Peso")]
            ).properties(height=300)
            st.altair_chart(chart_peso, use_container_width=True)
            
        # Grafico delle Pliche (Totale e Media o singole pliche) se presenti
        tot_col_candidates = [c for c in df_player.columns if "tot" in c.lower() or "somma" in c.lower()]
        media_col_candidates = [c for c in df_player.columns if "med" in c.lower()]
        
        if tot_col_candidates:
            t_col = tot_col_candidates[0]
            st.markdown("##### 📉 Andamento Somma Totale Pliche")
            chart_tot = alt.Chart(df_player).mark_line(point=True, strokeWidth=3, color="#f97316").encode(
                x=alt.X("DataControllo:N", title="Controllo / Data", sort=None),
                y=alt.Y(f"{t_col}:Q", title="Totale Pliche (mm)", scale=alt.Scale(zero=False)),
                tooltip=["DataControllo", alt.Tooltip(f"{t_col}:Q", title="Totale Pliche")]
            ).properties(height=300)
            st.altair_chart(chart_tot, use_container_width=True)

    if st.button("🏠 Torna alla Home", key="back_home_pliche"):
        st.session_state.page = "home"
        st.rerun()
