import streamlit as st
import pandas as pd
import altair as alt
import requests
import io

PLICHE_SHEET_ID = "1zH8w4hePJK531fxq0RGGX7az76EEz4c7vXWF5tCM1mc"

@st.cache_data(ttl=60)
def load_pliche_data():
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
        if str(sheet_name).strip().lower() == 'info':
            continue
            
        data_raw = str(sheet_name).strip()
        dt_parsed = pd.to_datetime(data_raw, errors="coerce")
        if pd.notna(dt_parsed):
            data_controllo = dt_parsed.strftime("%d/%m")
            data_sort = dt_parsed.strftime("%Y-%m-%d")
        else:
            data_controllo = data_raw
            data_sort = data_raw

        header_row_idx = None
        for i in range(min(len(df), 10)):
            row_vals = [str(val).strip().lower() for val in df.iloc[i].values]
            if any("giocatore" in val or "atleta" in val for val in row_vals):
                header_row_idx = i
                break
        
        if header_row_idx is None:
            continue
            
        sub_df = df.iloc[header_row_idx:].copy()
        sub_df.columns = sub_df.iloc[0]
        sub_df = sub_df.iloc[1:].reset_index(drop=True)
        sub_df = sub_df.loc[:, sub_df.columns.notna()]
        sub_df.columns = [str(c).strip() for c in sub_df.columns]
        
        label_col = sub_df.columns[0]
        player_cols = sub_df.columns[1:]
        
        for col in player_cols:
            player_name = str(col).strip()
            if not player_name or player_name.lower() == 'nan':
                continue
                
            p_data = {"Atleta": player_name, "DataControllo": data_controllo, "DataSort": data_sort}
            has_valid_data = False
            
            for idx, row in sub_df.iterrows():
                metric_name = str(row[label_col]).strip()
                if not metric_name or metric_name.lower() == 'nan':
                    continue
                val = row[col]
                if pd.notna(val) and str(val).strip() != "":
                    has_valid_data = True
                try:
                    val_num = float(str(val).replace(',', '.').strip())
                except Exception:
                    val_num = val
                p_data[metric_name] = val_num
                
            if has_valid_data:
                all_rows.append(p_data)
                
    if not all_rows:
        return pd.DataFrame()
        
    return pd.DataFrame(all_rows)

def render(allowed_athletes, ruoli_dict):
    st.markdown("### 📊 **Pliche Cutanee & Composizione Corporea**")
    
    if allowed_athletes == "ALL":
        st.success("🔓 Visualizzazione: Roster Completo")
    else:
        st.success(f"🔓 Visualizzazione Dedicata: {allowed_athletes[0]}")
        
    with st.spinner("Caricamento dati antropometrici..."):
        df_pliche = load_pliche_data()
        
    if df_pliche.empty:
        st.warning("⚠️ Nessun dato trovato o formato non riconosciuto.")
        if st.button("🏠 Torna alla Home"):
            st.session_state.page = "home"
            st.rerun()
        return

    if "Atleta" in df_pliche.columns:
        df_pliche["ATHLETE"] = df_pliche["Atleta"].astype(str).str.strip()
    else:
        return

    if allowed_athletes != "ALL":
        df_pliche = df_pliche[df_pliche["ATHLETE"].isin(allowed_athletes)]

    st.sidebar.divider()
    st.sidebar.header("🔍 Filtri Pliche")
    giocatori_list = sorted(df_pliche["ATHLETE"].unique())
    selected_player = st.sidebar.selectbox("Seleziona Giocatore", giocatori_list)

    df_player = df_pliche[df_pliche["ATHLETE"] == selected_player]
    if "DataSort" in df_player.columns:
        df_player = df_player.sort_values("DataSort")

    st.markdown(f"#### 👤 Atleta: **{selected_player}**")
    st.markdown("##### 📋 Storico Controlli (Date con misurazioni effettive)")
    
    cols_presenti = [c for c in df_player.columns if c not in ["Atleta", "ATHLETE", "DataSort"]]
    
    if not df_player.empty:
        st.dataframe(df_player[cols_presenti], use_container_width=True, hide_index=True)
        
        peso_col_candidates = [c for c in df_player.columns if "peso" in c.lower()]
        if peso_col_candidates:
            p_col = peso_col_candidates[0]
            st.markdown("##### ⚖️ Andamento Peso (Kg)")
            chart_peso = alt.Chart(df_player).mark_line(point=True, strokeWidth=3, color="#2563eb").encode(
                x=alt.X("DataControllo:N", title="Data (gg/mm)", sort=None),
                y=alt.Y(f"{p_col}:Q", title="Peso (Kg)", scale=alt.Scale(zero=False)),
                tooltip=["DataControllo", alt.Tooltip(f"{p_col}:Q", title="Peso")]
            ).properties(height=300)
            st.altair_chart(chart_peso, use_container_width=True)
            
        tot_col_candidates = [c for c in df_player.columns if "tot" in c.lower() or "somma" in c.lower()]
        if tot_col_candidates:
            t_col = tot_col_candidates[0]
            st.markdown("##### 📉 Andamento Somma Totale Pliche")
            chart_tot = alt.Chart(df_player).mark_line(point=True, strokeWidth=3, color="#f97316").encode(
                x=alt.X("DataControllo:N", title="Data (gg/mm)", sort=None),
                y=alt.Y(f"{t_col}:Q", title="Totale Pliche (mm)", scale=alt.Scale(zero=False)),
                tooltip=["DataControllo", alt.Tooltip(f"{t_col}:Q", title="Totale Pliche")]
            ).properties(height=300)
            st.altair_chart(chart_tot, use_container_width=True)

    if st.button("🏠 Torna alla Home", key="back_home_pliche"):
        st.session_state.page = "home"
        st.rerun()
