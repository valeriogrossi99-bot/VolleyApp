import glob
from urllib.parse import quote

import altair as alt
import pandas as pd
import streamlit as st

# =============================================================================
# CONFIGURAZIONE
# =============================================================================
st.set_page_config(
    page_title="Cuneo Volley Performance Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

LOGO_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10"
TEAM_URL = "https://cuneovolley.it/prima-squadra/giocatori"
SHEET_ID = "1ib2DrRfODly8HT_V8c2PRNdALYt1_vDCAbvtAK7U1aw"

st.markdown(
    f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    .stApp {{
        background-color: #ffffff;
        color: #1f2937;
    }}

    .logo-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 20px;
        margin-bottom: 10px;
    }}

    div[data-testid="stMetric"] {{
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }}

    div[data-testid="stMetric"] label {{
        color: #475569 !important;
        font-size: 0.95rem !important;
        font-weight: 600;
    }}

    div[data-testid="stMetricValue"] {{
        color: #2563eb !important;
        font-weight: 700 !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }}

    .player-card {{
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }}

    .player-title {{
        color: #0f172a;
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 5px;
    }}

    .player-role {{
        color: #2563eb;
        font-size: 1.1rem;
        font-weight: 700;
    }}

    div.stButton > button {{
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 35px 20px !important;
        height: auto !important;
        width: 100% !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.25s ease-in-out !important;
        white-space: pre-wrap !important;
        line-height: 1.5 !important;
    }}

    div.stButton > button:hover {{
        border-color: #2563eb !important;
        background-color: #ffffff !important;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12) !important;
        transform: translateY(-4px) !important;
    }}

    h1, h2, h3 {{color: #0f172a;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# SESSIONE E ACCESSI
# =============================================================================
if "page" not in st.session_state:
    st.session_state.page = "home"
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "pending_module" not in st.session_state:
    st.session_state.pending_module = None

ACCESS_CODES = {
    "CUNEO": "ALL",
    "FRACN": ["Nathan Feral"],
    "ITA-CN": ["Leandro Mosca"],
}

# =============================================================================
# ROSTER
# =============================================================================
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
    "Mimmo Cavaccini": "Libero",
    "Thibault Loubeyre": "Libero",
}

cognomi_to_full = {
    "Argilagos": "Bryan Argilagos",
    "Coscione": "Manuel Coscione",
    "Strehlau": "Alexandre Strehlau",
    "Champlin": "Ethan Champlin",
    "Giraudo": "Federico Giraudo",
    "Poriya": "Poriya Khanzadeh",
    "Khanzadeh": "Poriya Khanzadeh",
    "Feral": "Nathan Feral",
    "Sala": "Lorenzo Sala",
    "Barberio": "Emanuele Barberio",
    "Mosca": "Leandro Mosca",
    "Codarin": "Lorenzo Codarin",
    "Volpe": "Nicoló Volpe",
    "Cavaccini": "Mimmo Cavaccini",
    "Loubeyre": "Thibault Loubeyre",
}

player_bio = {
    "Bryan Argilagos": "Palleggiatore | Altezza: 200 cm | Classe 2007",
    "Manuel Coscione": "Palleggiatore | Altezza: 188 cm | Classe 1980",
    "Alexandre Strehlau": "Schiacciatore | Altezza: 199 cm | Classe 2004",
    "Ethan Champlin": "Schiacciatore | Altezza: 191 cm | Classe 2001",
    "Federico Giraudo": "Schiacciatore | Altezza: 198 cm | Classe 2007",
    "Poriya Khanzadeh": "Schiacciatore | Altezza: 202 cm | Classe 2004",
    "Nathan Feral": "Opposto | Altezza: 197 cm | Classe 2003",
    "Lorenzo Sala": "Opposto | Altezza: 200 cm | Classe 2002",
    "Emanuele Barberio": "Centrale | Altezza: 202 cm | Classe 2007",
    "Leandro Mosca": "Centrale | Altezza: 209 cm | Classe 2000",
    "Lorenzo Codarin": "Centrale | Altezza: 199 cm | Classe 1996",
    "Nicoló Volpe": "Centrale | Altezza: 193 cm | Classe 2003",
}

MATCH_DAYS = {
    "2026-10-18", "2026-10-25", "2026-11-01", "2026-11-04",
    "2026-11-08", "2026-11-22", "2026-11-29", "2026-12-02",
    "2026-12-06", "2026-12-13", "2026-12-20", "2026-12-26",
    "2027-01-03", "2027-01-10", "2027-01-13", "2027-01-17",
    "2027-01-24", "2027-01-31", "2027-02-14", "2027-02-21",
    "2027-02-24", "2027-02-28",
}

ANCHOR_MONDAY = pd.Timestamp("2026-10-05")

# =============================================================================
# FUNZIONI DI SUPPORTO
# =============================================================================
def get_custom_week(series):
    dates = pd.to_datetime(series, errors="coerce")
    week_num = 7 + ((dates - ANCHOR_MONDAY).dt.days // 7)
    result = pd.Series(pd.NA, index=series.index, dtype="string")
    valid = dates.notna()
    result.loc[valid] = "Settimana " + week_num.loc[valid].astype("Int64").astype(str)
    return result


def extract_week_num(value):
    try:
        return int(str(value).replace("Settimana ", ""))
    except (TypeError, ValueError):
        return -1


def clean_columns(df):
    """Pulisce le intestazioni e rende sempre univoci i nomi colonna."""
    df = df.copy()
    raw = [str(c).strip() for c in df.columns]
    counts = {}
    unique = []
    for name in raw:
        base = name or "COLONNA"
        count = counts.get(base, 0)
        unique.append(base if count == 0 else f"{base}__{count + 1}")
        counts[base] = count + 1
    df.columns = unique
    return df


def numeric_series(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip(),
        errors="coerce",
    )


def csv_files():
    return sorted(set(glob.glob("data/*.csv") + glob.glob("*.csv")))


def apply_access(df, allowed):
    if df.empty or allowed == "ALL" or "ATHLETE" not in df.columns:
        return df
    return df[df["ATHLETE"].isin(allowed)].copy()

# =============================================================================
# CARICAMENTO DATI
# =============================================================================
@st.cache_data
def load_jump_data():
    frames = []
    for file_path in csv_files():
        try:
            temp = clean_columns(pd.read_csv(file_path, sep=";"))
            required = {"NAME", "SURNAME", "DATE", "JUMP HEIGHT(cm)"}
            if required.issubset(temp.columns):
                frames.append(temp)
        except Exception:
            continue

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True, sort=False)
    df["JUMP HEIGHT(cm)"] = numeric_series(df["JUMP HEIGHT(cm)"])
    df = df.dropna(subset=["JUMP HEIGHT(cm)"]).copy()
    df["ATHLETE"] = (
        df["NAME"].fillna("").astype(str).str.strip()
        + " "
        + df["SURNAME"].fillna("").astype(str).str.strip()
    ).str.strip()
    df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")
    df["DATE_DT"] = pd.to_datetime(df["DATE"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["DATE_DT"]).copy()
    df["DATE_STR"] = df["DATE_DT"].dt.strftime("%Y-%m-%d")
    df["WEEK"] = get_custom_week(df["DATE_DT"])
    df["IS_MATCH"] = df["DATE_STR"].isin(MATCH_DAYS)

    df["JUMP_BAND"] = pd.cut(
        df["JUMP HEIGHT(cm)"],
        bins=[float("-inf"), 30, 50, 60, 70, float("inf")],
        right=True,
        include_lowest=True,
        labels=["JUMPS < 30", "JUMPS 30-50", "JUMPS 50-60", "JUMPS 60-70", "JUMPS > 70"],
    )
    return df


@st.cache_data
def load_load_data():
    frames = []
    load_markers = {"TONNAGE", "WEIGHT(kg)", "LOAD(kg)", "RPE"}
    for file_path in csv_files():
        try:
            temp = clean_columns(pd.read_csv(file_path, sep=";"))
            if load_markers.intersection(temp.columns):
                frames.append(temp)
        except Exception:
            continue

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True, sort=False)

    if {"NAME", "SURNAME"}.issubset(df.columns):
        df["ATHLETE"] = (
            df["NAME"].fillna("").astype(str).str.strip()
            + " "
            + df["SURNAME"].fillna("").astype(str).str.strip()
        ).str.strip()
    elif "ATHLETE" not in df.columns:
        df["ATHLETE"] = "Atleta Generico"

    df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")
    date_col = next((c for c in ["DATE", "Data", "DATA"] if c in df.columns), None)
    if date_col is None:
        return pd.DataFrame()

    df["DATE_DT"] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["DATE_DT"]).copy()
    df["DATE_STR"] = df["DATE_DT"].dt.strftime("%Y-%m-%d")
    df["WEEK"] = get_custom_week(df["DATE_DT"])

    if "TONNAGE" in df.columns:
        df["TOTAL_LOAD"] = numeric_series(df["TONNAGE"]).fillna(0)
    elif {"WEIGHT(kg)", "REPS"}.issubset(df.columns):
        df["TOTAL_LOAD"] = (
            numeric_series(df["WEIGHT(kg)"]).fillna(0)
            * numeric_series(df["REPS"]).fillna(0)
        )
    elif "LOAD(kg)" in df.columns:
        df["TOTAL_LOAD"] = numeric_series(df["LOAD(kg)"]).fillna(0)
    else:
        df["TOTAL_LOAD"] = 0.0
    return df


@st.cache_data(ttl=300)
def load_google_sheet_force():
    exercises = ["Back Squat", "Front Squat", "Stacco QB"]
    frames = []
    errors = []

    for exercise in exercises:
        try:
            sheet_name = quote(exercise, safe="")
            url = (
                f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
                f"?tqx=out:csv&sheet={sheet_name}"
            )
            temp = clean_columns(pd.read_csv(url))
            temp = temp.dropna(how="all").copy()

            athlete_col = next(
                (
                    c for c in temp.columns
                    if "atleta" in c.lower() or c.lower().startswith("unnamed")
                ),
                None,
            )
            if athlete_col is None:
                errors.append(f"{exercise}: colonna Atleta non trovata")
                continue

            if athlete_col != "Atleta":
                temp = temp.rename(columns={athlete_col: "Atleta"})

            # Dopo il rename garantisce nuovamente intestazioni univoche.
            temp = clean_columns(temp)
            temp["ESERCIZIO"] = exercise
            frames.append(temp)
        except Exception as exc:
            errors.append(f"{exercise}: {exc}")

    if not frames:
        return pd.DataFrame(), errors

    # clean_columns impedisce InvalidIndexError durante concat.
    frames = [clean_columns(frame).reset_index(drop=True) for frame in frames]
    df = pd.concat(frames, ignore_index=True, sort=False)

    if "Atleta" not in df.columns:
        return pd.DataFrame(), errors + ["Colonna Atleta assente dopo l'unione dei fogli"]

    df["Atleta"] = df["Atleta"].astype(str).str.strip()
    df = df[
        df["Atleta"].notna()
        & ~df["Atleta"].str.lower().isin({"", "nan", "atleta"})
    ].copy()

    numeric_cols = ["BW", "Peso usato", "Reps", "RIR", "1RM Teorico", "1RM/BW", "1RM Ideale"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = numeric_series(df[col]).fillna(0.0)
        else:
            df[col] = 0.0

    df["ATHLETE"] = df["Atleta"].map(cognomi_to_full).fillna(df["Atleta"])
    df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")
    return df, errors

# =============================================================================
# HOME
# =============================================================================
if st.session_state.page == "home":
    st.markdown(
        f"""
        <div class="logo-container">
            <img src="{LOGO_URL}" width="140" alt="Cuneo Volley">
        </div>
        <h1 style="text-align:center;font-size:2.8rem;margin:10px 0 5px;">Cuneo Volley</h1>
        <p style="text-align:center;color:#64748b;font-size:1.1rem;font-weight:500;margin-bottom:30px;">
            Performance &amp; Analytics Hub
        </p>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.pending_module:
        st.warning(
            f"🔑 **Inserisci il codice PIN per accedere a "
            f"{st.session_state.pending_module.upper()}**"
        )
        col_pin, col_btn = st.columns([3, 1])
        with col_pin:
            entered_pin = st.text_input(
                "Codice di sicurezza:", type="password", key="pin_input"
            ).strip()
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Conferma PIN 🔓", use_container_width=True):
                if entered_pin in ACCESS_CODES:
                    st.session_state.auth_token = entered_pin
                    st.session_state.page = st.session_state.pending_module
                    st.session_state.pending_module = None
                    st.rerun()
                else:
                    st.error("❌ Codice non valido. Riprova.")
        if st.button("❌ Annulla"):
            st.session_state.pending_module = None
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "🚀\n\nDataJump\n\nMonitoraggio Salti, Elevazione & Distribuzione Fasce",
                key="btn_jump",
                use_container_width=True,
            ):
                if st.session_state.auth_token:
                    st.session_state.page = "datajump"
                else:
                    st.session_state.pending_module = "datajump"
                st.rerun()
        with col2:
            if st.button(
                "🏋️‍♂️\n\nDataLoad\n\nMonitoraggio Carichi, Massimali & Valutazione Forza",
                key="btn_load",
                use_container_width=True,
            ):
                if st.session_state.auth_token:
                    st.session_state.page = "dataload"
                else:
                    st.session_state.pending_module = "dataload"
                st.rerun()

# =============================================================================
# DATAJUMP
# =============================================================================
elif st.session_state.page == "datajump":
    h1, h2 = st.columns([8, 2])
    with h1:
        st.markdown("### 🚀 **DataJump** | Monitoraggio Salti & Elevazione")
    with h2:
        if st.button("🏠 Torna alla Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

    allowed = ACCESS_CODES.get(st.session_state.auth_token, [])
    if allowed == "ALL":
        st.sidebar.success("🔓 Accesso completo: roster Cuneo Volley")
    else:
        st.sidebar.success(f"🔓 Accesso riservato: {', '.join(allowed)}")

    df_jump = apply_access(load_jump_data(), allowed)
    if df_jump.empty:
        st.warning("⚠️ Nessun dato valido relativo ai salti trovato nei file CSV.")
        st.stop()

    st.sidebar.divider()
    st.sidebar.header("🔍 Filtri selezione e confronto")
    roles = sorted(df_jump["ROLE"].dropna().unique())
    selected_roles = st.sidebar.multiselect("Filtra per ruolo", roles)
    df_f = df_jump[df_jump["ROLE"].isin(selected_roles)].copy() if selected_roles else df_jump.copy()

    players = sorted(df_f["ATHLETE"].dropna().unique())
    selected_players = st.sidebar.multiselect("Seleziona giocatori", players)
    if selected_players:
        df_f = df_f[df_f["ATHLETE"].isin(selected_players)].copy()

    weeks = sorted(df_f["WEEK"].dropna().unique(), key=extract_week_num, reverse=True)
    selected_weeks = st.sidebar.multiselect("Settimane di lavoro", weeks)
    if selected_weeks:
        df_f = df_f[df_f["WEEK"].isin(selected_weeks)].copy()

    sessions = sorted(df_f["DATE_STR"].dropna().unique(), reverse=True)
    selected_sessions = st.sidebar.multiselect("Date sedute", sessions)
    if selected_sessions:
        df_f = df_f[df_f["DATE_STR"].isin(selected_sessions)].copy()

    if len(selected_players) == 1:
        player = selected_players[0]
        st.markdown(
            f"""
            <div class="player-card">
                <div class="player-title">🛡️ {player}</div>
                <div class="player-role">Ruolo: {ruoli_dict.get(player, 'Atleta')}</div>
                <p style="color:#475569;margin:8px 0 12px;">
                    {player_bio.get(player, 'Cuneo Volley Prima Squadra')}
                </p>
                <a href="{TEAM_URL}" target="_blank" style="color:#2563eb;text-decoration:none;font-weight:600;">
                    🔗 Vai alla scheda ufficiale Cuneo Volley →
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif len(selected_players) > 1:
        st.info(f"📊 Modalità confronto: {len(selected_players)} giocatori selezionati.")

    daily = (
        df_f.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"], dropna=False)
        .agg(
            SALTI_GIORNO=("JUMP HEIGHT(cm)", "count"),
            MAX_GIORNO=("JUMP HEIGHT(cm)", "max"),
            MEDIA_GIORNO=("JUMP HEIGHT(cm)", "mean"),
            IS_MATCH=("IS_MATCH", "max"),
        )
        .reset_index()
    )
    weekly = (
        df_f.groupby(["ATHLETE", "ROLE", "WEEK"], dropna=False)
        .agg(
            SALTI_SETTIMANA=("JUMP HEIGHT(cm)", "count"),
            MAX_SETTIMANA=("JUMP HEIGHT(cm)", "max"),
            MEDIA_SETTIMANA=("JUMP HEIGHT(cm)", "mean"),
        )
        .reset_index()
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totale salti", f"{len(df_f):,}".replace(",", "."))
    c2.metric("Salto max", f"{df_f['JUMP HEIGHT(cm)'].max():.1f} cm")
    c3.metric("Media salti", f"{df_f['JUMP HEIGHT(cm)'].mean():.1f} cm")
    c4.metric("Giocatori monitorati", df_f["ATHLETE"].nunique())
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Andamento giornaliero",
        "🗓️ Andamento settimanale",
        "⚔️ Confronto giocatori",
        "🎯 Distribuzione fasce",
    ])

    with tab1:
        if daily.empty:
            st.info("Nessun dato per i filtri selezionati.")
        else:
            st.markdown("##### Volume salti per data e giocatore")
            st.altair_chart(
                alt.Chart(daily).mark_bar().encode(
                    x=alt.X("DATE_STR:N", title="Data seduta", sort="ascending"),
                    y=alt.Y("SALTI_GIORNO:Q", title="Numero salti"),
                    color=alt.Color("ATHLETE:N", title="Giocatore"),
                    tooltip=["DATE_STR", "ATHLETE", "SALTI_GIORNO", "MAX_GIORNO"],
                ).properties(height=380),
                use_container_width=True,
            )
            st.markdown("##### Salto massimo")
            st.altair_chart(
                alt.Chart(daily).mark_line(point=True).encode(
                    x=alt.X("DATE_STR:N", title="Data seduta", sort="ascending"),
                    y=alt.Y("MAX_GIORNO:Q", title="Salto max (cm)"),
                    color=alt.Color("ATHLETE:N", title="Giocatore"),
                    tooltip=["DATE_STR", "ATHLETE", "MAX_GIORNO"],
                ).properties(height=380),
                use_container_width=True,
            )

    with tab2:
        if weekly.empty:
            st.info("Nessun dato per i filtri selezionati.")
        else:
            week_order = sorted(weekly["WEEK"].dropna().unique(), key=extract_week_num)
            st.altair_chart(
                alt.Chart(weekly).mark_bar().encode(
                    x=alt.X("WEEK:N", title="Settimana", sort=week_order),
                    y=alt.Y("SALTI_SETTIMANA:Q", title="Numero salti"),
                    color=alt.Color("ATHLETE:N", title="Giocatore"),
                    tooltip=["WEEK", "ATHLETE", "SALTI_SETTIMANA"],
                ).properties(height=380),
                use_container_width=True,
            )

    with tab3:
        comp = (
            df_f.groupby(["ATHLETE", "ROLE"])
            .agg(
                TOT_SALTI=("JUMP HEIGHT(cm)", "count"),
                MAX_SALTO=("JUMP HEIGHT(cm)", "max"),
                MEDIA_SALTO=("JUMP HEIGHT(cm)", "mean"),
            )
            .reset_index()
        )
        left, right = st.columns(2)
        with left:
            st.altair_chart(
                alt.Chart(comp).mark_bar(color="#2563eb").encode(
                    x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                    y=alt.Y("TOT_SALTI:Q", title="Totale salti"),
                    tooltip=["ATHLETE", "TOT_SALTI", "MEDIA_SALTO"],
                ).properties(height=350),
                use_container_width=True,
            )
        with right:
            st.altair_chart(
                alt.Chart(comp).mark_bar(color="#f97316").encode(
                    x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                    y=alt.Y("MAX_SALTO:Q", title="Salto max (cm)"),
                    tooltip=["ATHLETE", "MAX_SALTO"],
                ).properties(height=350),
                use_container_width=True,
            )

    with tab4:
        order = ["JUMPS < 30", "JUMPS 30-50", "JUMPS 50-60", "JUMPS 60-70", "JUMPS > 70"]
        bands = df_f.groupby(["JUMP_BAND", "ATHLETE"], observed=True).size().reset_index(name="Numero Salti")
        st.altair_chart(
            alt.Chart(bands).mark_bar().encode(
                x=alt.X("JUMP_BAND:N", sort=order, title="Fascia"),
                y=alt.Y("Numero Salti:Q", title="Numero salti"),
                color=alt.Color("ATHLETE:N", title="Giocatore"),
                tooltip=["JUMP_BAND", "ATHLETE", "Numero Salti"],
            ).properties(height=400),
            use_container_width=True,
        )

# =============================================================================
# DATALOAD
# =============================================================================
elif st.session_state.page == "dataload":
    h1, h2 = st.columns([8, 2])
    with h1:
        st.markdown("### 🏋️‍♂️ **DataLoad** | Monitoraggio Carichi & Valutazione Forza")
    with h2:
        if st.button("🏠 Torna alla Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

    allowed = ACCESS_CODES.get(st.session_state.auth_token, [])
    if allowed == "ALL":
        st.sidebar.success("🔓 Accesso completo: roster Cuneo Volley")
    else:
        st.sidebar.success(f"🔓 Accesso riservato: {', '.join(allowed)}")

    df_load = apply_access(load_load_data(), allowed)
    df_force, force_errors = load_google_sheet_force()
    df_force = apply_access(df_force, allowed)

    st.sidebar.divider()
    st.sidebar.header("🔍 Filtri selezione e confronto")

    force_tab, daily_tab, weekly_tab, compare_tab = st.tabs([
        "🏋️ Valutazione Forza & 1RM",
        "📊 Tonnellaggio Giornaliero",
        "🗓️ Carico Settimanale",
        "⚔️ Confronto Carichi",
    ])

    with force_tab:
        st.markdown("##### Valutazione forza e massimali teorici")
        if force_errors:
            with st.expander("Dettagli caricamento fogli Google"):
                for message in force_errors:
                    st.warning(message)

        if df_force.empty or "ESERCIZIO" not in df_force.columns:
            st.info("ℹ️ Impossibile caricare dati validi dal foglio Google.")
        else:
            exercises = sorted(df_force["ESERCIZIO"].dropna().unique())
            selected_ex = st.selectbox("Seleziona esercizio:", exercises)
            force_sub = df_force[df_force["ESERCIZIO"] == selected_ex].copy()
            athletes = sorted(force_sub["ATHLETE"].dropna().unique())
            selected = st.multiselect("Filtra per giocatore/i:", athletes, default=athletes)
            if selected:
                force_sub = force_sub[force_sub["ATHLETE"].isin(selected)].copy()

            display_cols = [c for c in [
                "ATHLETE", "ROLE", "BW", "Peso usato", "Reps", "RIR",
                "1RM Teorico", "1RM/BW", "1RM Ideale"
            ] if c in force_sub.columns]
            st.dataframe(force_sub[display_cols], use_container_width=True, hide_index=True)

            left, right = st.columns(2)
            with left:
                st.write(f"**1RM teorico (kg) | {selected_ex}**")
                st.altair_chart(
                    alt.Chart(force_sub).mark_bar(color="#2563eb").encode(
                        x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                        y=alt.Y("1RM Teorico:Q", title="1RM teorico (kg)"),
                        tooltip=[c for c in ["ATHLETE", "BW", "Peso usato", "Reps", "1RM Teorico", "1RM/BW"] if c in force_sub.columns],
                    ).properties(height=360),
                    use_container_width=True,
                )
            with right:
                st.write(f"**Forza relativa (1RM/BW) | {selected_ex}**")
                st.altair_chart(
                    alt.Chart(force_sub).mark_bar(color="#16a34a").encode(
                        x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                        y=alt.Y("1RM/BW:Q", title="Forza relativa (xBW)"),
                        tooltip=[c for c in ["ATHLETE", "BW", "1RM/BW", "1RM Teorico"] if c in force_sub.columns],
                    ).properties(height=360),
                    use_container_width=True,
                )

    with daily_tab:
        if df_load.empty:
            st.info("ℹ️ Nessun dato di tonnellaggio giornaliero disponibile.")
        else:
            daily_load = (
                df_load.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"], dropna=False)
                .agg(TONNELLAGGIO_GIORNO=("TOTAL_LOAD", "sum"), CARICO_MAX=("TOTAL_LOAD", "max"))
                .reset_index()
            )
            st.altair_chart(
                alt.Chart(daily_load).mark_bar().encode(
                    x=alt.X("DATE_STR:N", title="Data seduta", sort="ascending"),
                    y=alt.Y("TONNELLAGGIO_GIORNO:Q", title="Tonnellaggio totale (kg)"),
                    color=alt.Color("ATHLETE:N", title="Giocatore"),
                    tooltip=["DATE_STR", "ATHLETE", "TONNELLAGGIO_GIORNO"],
                ).properties(height=380),
                use_container_width=True,
            )

    with weekly_tab:
        if df_load.empty:
            st.info("ℹ️ Nessun dato di tonnellaggio settimanale disponibile.")
        else:
            weekly_load = (
                df_load.groupby(["ATHLETE", "ROLE", "WEEK"], dropna=False)
                .agg(TONNELLAGGIO_SETTIMANA=("TOTAL_LOAD", "sum"), CARICO_MAX_SETTIMANA=("TOTAL_LOAD", "max"))
                .reset_index()
            )
            week_order = sorted(weekly_load["WEEK"].dropna().unique(), key=extract_week_num)
            st.altair_chart(
                alt.Chart(weekly_load).mark_bar().encode(
                    x=alt.X("WEEK:N", title="Settimana", sort=week_order),
                    y=alt.Y("TONNELLAGGIO_SETTIMANA:Q", title="Tonnellaggio settimanale (kg)"),
                    color=alt.Color("ATHLETE:N", title="Giocatore"),
                    tooltip=["WEEK", "ATHLETE", "TONNELLAGGIO_SETTIMANA"],
                ).properties(height=380),
                use_container_width=True,
            )

    with compare_tab:
        if df_load.empty:
            st.info("ℹ️ Nessun dato disponibile per il confronto.")
        else:
            comp = (
                df_load.groupby(["ATHLETE", "ROLE"])
                .agg(TOT_TONN=("TOTAL_LOAD", "sum"), MAX_TONN=("TOTAL_LOAD", "max"))
                .reset_index()
            )
            left, right = st.columns(2)
            with left:
                st.altair_chart(
                    alt.Chart(comp).mark_bar(color="#2563eb").encode(
                        x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                        y=alt.Y("TOT_TONN:Q", title="Volume totale (kg)"),
                        tooltip=["ATHLETE", "TOT_TONN"],
                    ).properties(height=350),
                    use_container_width=True,
                )
            with right:
                st.altair_chart(
                    alt.Chart(comp).mark_bar(color="#f97316").encode(
                        x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                        y=alt.Y("MAX_TONN:Q", title="Picco carico (kg)"),
                        tooltip=["ATHLETE", "MAX_TONN"],
                    ).properties(height=350),
                    use_container_width=True,
                )
