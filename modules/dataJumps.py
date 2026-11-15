import streamlit as st
import pandas as pd
import altair as alt
import html as html_lib
import glob
import os
from urllib.parse import quote

# Costanti e dizionari condivisi
MATCH_DAYS = {
    "2026-10-18", "2026-10-25", "2026-11-01", "2026-11-04", "2026-11-08",
    "2026-11-22", "2026-11-29", "2026-12-02", "2026-12-06", "2026-12-13",
    "2026-12-20", "2026-12-26", "2027-01-03", "2027-01-10", "2027-01-13",
    "2027-01-17", "2027-01-24", "2027-01-31", "2027-02-14", "2027-02-21",
    "2027-02-24", "2027-02-28"
}

ANCHOR_MONDAY = pd.to_datetime("2026-10-05")
TIME_COLUMNS = {"TIME", "ORA", "ORARIO", "HOUR"}
GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
BAND_ORDER = ["JUMPS < 30", "JUMPS 30-50", "JUMPS 50-60", "JUMPS 60-70", "JUMPS > 70"]

LEGA_BASE = "https://www.legavolley.it"
LEGA_TEAM_ID = 6863
CUNEO_ROSTER_URL = "https://cuneovolley.it/prima-squadra/giocatori"

player_info = {
    "Bryan Argilagos": {"bio": "Palleggiatore | Altezza: 200 cm | Classe 2007"},
    "Manuel Coscione": {"bio": "Palleggiatore | Altezza: 188 cm | Classe 1980"},
    "Alexandre Strehlau": {"bio": "Schiacciatore | Altezza: 199 cm | Classe 2004"},
    "Ethan Champlin": {"bio": "Schiacciatore | Altezza: 191 cm | Classe 2001"},
    "Federico Giraudo": {"bio": "Schiacciatore | Altezza: 198 cm | Classe 2007"},
    "Poriya Khanzadeh": {"bio": "Schiacciatore | Altezza: 202 cm | Classe 2004"},
    "Nathan Feral": {"bio": "Opposto | Altezza: 197 cm | Classe 2003"},
    "Lorenzo Sala": {"bio": "Opposto | Altezza: 200 cm | Classe 2002"},
    "Emanuele Barberio": {"bio": "Centrale | Altezza: 202 cm | Classe 2007"},
    "Leandro Mosca": {"bio": "Centrale | Altezza: 209 cm | Classe 2000"},
    "Lorenzo Codarin": {"bio": "Centrale | Altezza: 199 cm | Classe 1996"},
    "Nicoló Volpe": {"bio": "Centrale | Altezza: 193 cm | Classe 2003"},
    "Mimmo Cavaccini": {"bio": "Libero | Altezza: 168 cm | Classe 1987"},
    "Thibault Loubeyre": {"bio": "Libero | Altezza: 178 cm | Classe 2001"}
}

def get_csv_files():
    files = glob.glob("data/*.csv") + glob.glob("data/*.CSV") + glob.glob("*.csv") + glob.glob("*.CSV")
    return sorted(set(files))

def get_custom_week(dt_series):
    days_diff = (dt_series.dt.normalize() - ANCHOR_MONDAY).dt.days
    week_offset = days_diff // 7
    return "Settimana " + (7 + week_offset).astype(int).astype(str)

def extract_week_num(w_str):
    try:
        return int(w_str.replace("Settimana ", ""))
    except Exception:
        return 0

@st.cache_data(ttl=60)
def load_jump_data():
    files = get_csv_files()
    df_list = []
    for f in files:
        try:
            temp = pd.read_csv(f, sep=";")
            temp.columns = temp.columns.str.strip()
            if "JUMP HEIGHT(cm)" in temp.columns:
                df_list.append(temp)
        except Exception:
            pass
    if not df_list:
        return pd.DataFrame()
    df = pd.concat(df_list, ignore_index=True)
    df.columns = df.columns.str.strip()
    df["JUMP HEIGHT(cm)"] = pd.to_numeric(df["JUMP HEIGHT(cm)"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    df = df.dropna(subset=["JUMP HEIGHT(cm)"]).copy()
    
    from_name = df["NAME"].astype(str).str.strip() + " " + df["SURNAME"].astype(str).str.strip()
    df["ATHLETE"] = from_name
    
    # Ruoli predefiniti di fallback
    ruoli_dict = {
        "Bryan Argilagos": "Palleggiatore", "Manuel Coscione": "Palleggiatore",
        "Alexandre Strehlau": "Schiacciatore", "Ethan Champlin": "Schiacciatore",
        "Federico Giraudo": "Schiacciatore", "Poriya Khanzadeh": "Schiacciatore",
        "Nathan Feral": "Opposto", "Lorenzo Sala": "Opposto",
        "Emanuele Barberio": "Centrale", "Leandro Mosca": "Centrale",
        "Lorenzo Codarin": "Centrale", "Nicoló Volpe": "Centrale",
        "Mimmo Cavaccini": "Libero", "Thibault Loubeyre": "Libero"
    }
    df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")
    df["DATE_DT"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df.dropna(subset=["DATE_DT"]).copy()
    
    time_col = next((c for c in df.columns if c.upper() in TIME_COLUMNS), None)
    date_has_time = ((df["DATE_DT"].dt.hour != 0) | (df["DATE_DT"].dt.minute != 0)).any()
    df["DATETIME"] = df["DATE_DT"]
    df["HAS_TIME"] = bool(date_has_time)
    
    if not date_has_time and time_col is not None:
        combined = pd.to_datetime(df["DATE_DT"].dt.strftime("%Y-%m-%d") + " " + df[time_col].astype(str).str.strip(), errors="coerce")
        if combined.notna().any():
            df["DATETIME"] = combined.fillna(df["DATE_DT"])
            df["HAS_TIME"] = True
            
    df["DATE_DT"] = df["DATE_DT"].dt.normalize()
    df["DATE_STR"] = df["DATE_DT"].dt.strftime("%Y-%m-%d")
    df["WEEK"] = get_custom_week(df["DATE_DT"])
    df["IS_MATCH"] = df["DATE_STR"].isin(MATCH_DAYS)
    
    def classify_jump(h):
        try:
            val = float(h)
        except Exception:
            return "Altro"
        if val < 30: return "JUMPS < 30"
        elif 30 <= val <= 50: return "JUMPS 30-50"
        elif 50 < val <= 60: return "JUMPS 50-60"
        elif 60 < val <= 70: return "JUMPS 60-70"
        else: return "JUMPS > 70"
        
    df["JUMP_BAND"] = df["JUMP HEIGHT(cm)"].apply(classify_jump)
    return df

def render(allowed_athletes, ruoli_dict):
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1:
        st.markdown("### 🚀 **DataJump** — Monitoraggio Salti & Elevazione")
    with col_h2:
        if st.button("🏠 Torna alla Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

    if allowed_athletes == "ALL":
        st.sidebar.success("🔓 Visualizzazione: Roster Completo")
    else:
        st.sidebar.success(f"🔓 Visualizzazione Dedicata: {allowed_athletes[0]}")

    df_jump = load_jump_data()
    if df_jump.empty:
        st.warning("⚠️ Nessun file CSV relativo ai salti trovato.")
        if st.button("🏠 Torna alla Home", key="home_jump_err"):
            st.session_state.page = "home"
            st.rerun()
        return

    st.sidebar.caption(f"📁 {len(get_csv_files())} file CSV trovati · {df_jump['DATE_STR'].nunique()} sedute caricate")

    if allowed_athletes != "ALL":
        df_jump = df_jump[df_jump["ATHLETE"].isin(allowed_athletes)]

    st.sidebar.divider()
    st.sidebar.header("🔍 Filtri Selezione & Confronto")
    ruoli_list = sorted(list(set(df_jump["ROLE"].unique())))
    selected_roles = st.sidebar.multiselect("Filtra per Ruolo", ruoli_list)
    df_f = df_jump.copy()
    if selected_roles:
        df_f = df_f[df_f["ROLE"].isin(selected_roles)]

    giocatori_list = sorted(df_f["ATHLETE"].unique())
    selected_players = st.sidebar.multiselect("Seleziona Giocatori da Analizzare / Confrontare", giocatori_list)
    if selected_players:
        df_f = df_f[df_f["ATHLETE"].isin(selected_players)]

    df_base = df_f.copy()

    unique_weeks = sorted([w for w in df_f["WEEK"].unique() if pd.notna(w)], key=extract_week_num, reverse=True)
    selected_weeks = st.sidebar.multiselect("Settimane di Lavoro", unique_weeks)
    if selected_weeks:
        df_f = df_f[df_f["WEEK"].isin(selected_weeks)]

    sessioni_list = sorted([d for d in df_f["DATE_STR"].unique() if pd.notna(d)], reverse=True)
    selected_sessions = st.sidebar.multiselect("Date Sedute", sessioni_list)
    if selected_sessions:
        df_f = df_f[df_f["DATE_STR"].isin(selected_sessions)]

    single_player_target = selected_players[0] if selected_players and len(selected_players) == 1 else (allowed_athletes[0] if allowed_athletes != "ALL" else None)

    if single_player_target:
        p = single_player_target
        role_val = ruoli_dict.get(p, "Atleta")
        details = player_info.get(p, {})
        bio_val = details.get("bio", "Cuneo Volley Prima Squadra")
        link_val = f"{LEGA_BASE}/ricerca/?Search={quote(p.split()[-1])}&TipoOgg=ATL&FindAll=0"

        st.markdown(f"""
            <div style="background-color:#f8fafc;border:1px solid #e2e8f0;padding:20px;border-radius:14px;margin-bottom:20px;">
                <div style="font-size:1.6rem;font-weight:800;color:#0f172a;">{html_lib.escape(p)}</div>
                <div style="color:#2563eb;font-weight:700;">Ruolo: {html_lib.escape(role_val)}</div>
                <p style="color:#475569;margin-top:5px;">{html_lib.escape(bio_val)}</p>
                <a href="{link_val}" target="_blank" style="color:#2563eb;text-decoration:none;font-weight:600;">🔗 Vai alla scheda ufficiale su Lega Pallavolo Serie A →</a>
            </div>
        """, unsafe_allow_html=True)

    daily_summary = df_jump.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"]).agg(
        SALTI_GIORNO=("JUMP HEIGHT(cm)", "count"),
        MAX_GIORNO=("JUMP HEIGHT(cm)", "max"),
        MEDIA_GIORNO=("JUMP HEIGHT(cm)", "mean"),
        IS_MATCH=("IS_MATCH", "max")
    ).reset_index()

    weekly_summary = df_jump.groupby(["ATHLETE", "ROLE", "WEEK"]).agg(
        SALTI_SETTIMANA=("JUMP HEIGHT(cm)", "count"),
        MAX_SETTIMANA=("JUMP HEIGHT(cm)", "max"),
        MEDIA_SETTIMANA=("JUMP HEIGHT(cm)", "mean")
    ).reset_index()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totale Salti", f"{daily_summary['SALTI_GIORNO'].sum() if not daily_summary.empty else 0}")
    c2.metric("Salto Max", f"{daily_summary['MAX_GIORNO'].max() if not daily_summary.empty else 0:.1f} cm")
    c3.metric("Media Salti", f"{daily_summary['MEDIA_GIORNO'].mean() if not daily_summary.empty else 0:.1f} cm")
    c4.metric("Giocatori Monitorati", f"{len(df_f['ATHLETE'].unique()) if not df_f.empty else 0}")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Andamento Giornaliero", "🗓️ Andamento Settimanale",
        "⚔️ Confronto Giocatori", "🎯 Distribuzione Fasce", "🆚 Confronto Settimane"
    ])

    with tab1:
        if not daily_summary.empty:
            st.markdown("##### 🔵 Volume Salti per Data e Giocatore — ultime 7 sedute")
            ultime_date = sorted(daily_summary["DATE_STR"].unique())[-7:]
            daily_recent = daily_summary[daily_summary["DATE_STR"].isin(ultime_date)]
            match_dates = daily_recent[daily_recent["IS_MATCH"].astype(bool)][["DATE_STR"]].drop_duplicates()
            
            bars1 = alt.Chart(daily_recent).mark_bar().encode(
                x=alt.X("DATE_STR:N", title="Data Seduta"),
                y=alt.Y("SALTI_GIORNO:Q", title="Nr. Salti"),
                color=alt.Color("ATHLETE:N", title="Giocatore"),
                tooltip=["DATE_STR", "ATHLETE", "SALTI_GIORNO", "MAX_GIORNO"]
            )
            if match_dates.empty:
                chart1 = bars1.properties(height=380)
            else:
                match_bg = alt.Chart(match_dates).mark_rect(color="#f97316", opacity=0.2).encode(
                    x=alt.X("DATE_STR:N", title="Data Seduta"), y=alt.value(0), y2=alt.value(380)
                )
                chart1 = alt.layer(match_bg, bars1).properties(height=380)
            st.altair_chart(chart1, use_container_width=True)

    with tab2:
        if not weekly_summary.empty:
            st.markdown("##### 🔵 Volume Salti Settimanali")
            chart_w = alt.Chart(weekly_summary).mark_bar().encode(
                x=alt.X("WEEK:N", title="Settimana"),
                y=alt.Y("SALTI_SETTIMANA:Q", title="Nr. Salti"),
                color=alt.Color("ATHLETE:N", title="Giocatore"),
                tooltip=["WEEK", "ATHLETE", "SALTI_SETTIMANA"]
            ).properties(height=380)
            st.altair_chart(chart_w, use_container_width=True)

    with tab3:
        if not df_f.empty:
            comp_df = df_f.groupby(["ATHLETE", "ROLE"]).agg(
                TOT_SALTI=("JUMP HEIGHT(cm)", "count"),
                MAX_SALTO=("JUMP HEIGHT(cm)", "max"),
                MEDIA_SALTO=("JUMP HEIGHT(cm)", "mean")
            ).reset_index()
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Totale Salti per Giocatore**")
                st.altair_chart(alt.Chart(comp_df).mark_bar(color="#2563eb").encode(
                    x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                    y=alt.Y("TOT_SALTI:Q", title="Totale Salti"),
                    tooltip=["ATHLETE", "TOT_SALTI"]
                ).properties(height=350), use_container_width=True)
            with col_b:
                st.write("**Salto Max (cm) per Giocatore**")
                st.altair_chart(alt.Chart(comp_df).mark_bar(color="#f97316").encode(
                    x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                    y=alt.Y("MAX_SALTO:Q", title="Salto Max (cm)"),
                    tooltip=["ATHLETE", "MAX_SALTO"]
                ).properties(height=350), use_container_width=True)

    with tab4:
        if not df_f.empty:
            band_comp = df_f.groupby(["JUMP_BAND", "ATHLETE"]).size().reset_index(name="Numero Salti")
            chart_b = alt.Chart(band_comp).mark_bar().encode(
                x=alt.X("JUMP_BAND:N", sort=BAND_ORDER, title="Fascia"),
                y=alt.Y("Numero Salti:Q"),
                color=alt.Color("ATHLETE:N", title="Giocatore"),
                tooltip=["JUMP_BAND", "ATHLETE", "Numero Salti"]
            ).properties(height=400)
            st.altair_chart(chart_b, use_container_width=True)

    with tab5:
        st.markdown("##### 🆚 Confronto tra due settimane di lavoro")
        settimane_cmp = sorted([w for w in df_base["WEEK"].unique() if pd.notna(w)], key=extract_week_num, reverse=True)
        if len(settimane_cmp) < 2:
            st.info("Servono dati di almeno due settimane per fare il confronto.")
        else:
            col_wa, col_wb = st.columns(2)
            with col_wa: week_a = st.selectbox("Settimana A", settimane_cmp, index=1, key="cmp_week_a")
            with col_wb: week_b = st.selectbox("Settimana B", settimane_cmp, index=0, key="cmp_week_b")
            
            if week_a != week_b:
                df_a = df_base[df_base["WEEK"] == week_a]
                df_b = df_base[df_base["WEEK"] == week_b]
                st.caption(f"Confronto attivo tra {week_a} e {week_b}")
