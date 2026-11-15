import streamlit as st
import pandas as pd
import altair as alt
import glob
import os
import re
import html as html_lib
import base64
import requests
import unicodedata
from urllib.parse import quote, urljoin

# ------------------------------------------------------------------------------
# Configurazione e Dizionari originali
# ------------------------------------------------------------------------------
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

MATCH_DAYS = {
    "2026-10-18", "2026-10-25", "2026-11-01", "2026-11-04", "2026-11-08",
    "2026-11-22", "2026-11-29", "2026-12-02", "2026-12-06", "2026-12-13",
    "2026-12-20", "2026-12-26", "2027-01-03", "2027-01-10", "2027-01-13",
    "2027-01-17", "2027-01-24", "2027-01-31", "2027-02-14", "2027-02-21",
    "2027-02-24", "2027-02-28",
}

ANCHOR_MONDAY = pd.to_datetime("2026-10-05")
TIME_COLUMNS = {"TIME", "ORA", "ORARIO", "HOUR"}
GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
BAND_ORDER = ["JUMPS < 30", "JUMPS 30-50", "JUMPS 50-60", "JUMPS 60-70", "JUMPS > 70"]

LEGA_BASE = "https://www.legavolley.it"
LEGA_TEAM_ID = 6863
CUNEO_ROSTER_URL = "https://cuneovolley.it/prima-squadra/giocatori"
PHOTO_SOURCE_ORDER = ["cuneo", "lega"]
REQ_HEADERS = {"User-Agent": "Mozilla/5.0 (Cuneo Volley Performance Hub)"}

LEGA_PLAYER_IDS = {
    "Bryan Argilagos": "ARG-BRY-07", "Manuel Coscione": "COS-MAN-80",
    "Alexandre Strehlau": "STR-ALE-04", "Ethan Champlin": "CHA-ETH-01",
    "Federico Giraudo": "GIR-FED-07", "Poriya Khanzadeh": "KHA-POR-04",
    "Nathan Feral": "FER-NAT-03", "Lorenzo Sala": "SAL-LOR-02",
    "Emanuele Barberio": "BAR-EMA-07", "Leandro Mosca": "MOS-LEA-00",
    "Lorenzo Codarin": "COD-LOR-96", "Nicoló Volpe": "VOL-NIC-03",
    "Mimmo Cavaccini": "CAV-DOM-87", "Thibault Loubeyre": "LOU-THI-01",
}

# ------------------------------------------------------------------------------
# Funzioni originali
# ------------------------------------------------------------------------------
def _ascii_lower(text):
    text = unicodedata.normalize("NFKD", str(text))
    return text.encode("ascii", "ignore").decode().lower()

def _slug(text):
    return re.sub(r"[^a-z]", "", _ascii_lower(text))

def _tokens(text):
    return {t for t in re.split(r"[^a-z]+", _ascii_lower(text)) if t}

SURNAME_TO_PLAYER = {_slug(n.split()[-1]): n for n in ruoli_dict}

def _html_attr(tag, names):
    for n in names:
        m = re.search(rf"(?<![\w-]){n}\s*=\s*[\"']([^\"']*)[\"']", tag, flags=re.I)
        if m and m.group(1).strip():
            return html_lib.unescape(m.group(1).strip())
    return None

def _fetch_html(url, timeout=10):
    try:
        r = requests.get(url, headers=REQ_HEADERS, timeout=timeout)
        if r.status_code == 200: return r.text
    except Exception: pass
    return ""

def _download_image(url, max_bytes=6_000_000):
    try:
        r = requests.get(url, headers=REQ_HEADERS, timeout=12)
        ctype = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if r.status_code != 200 or not ctype.startswith("image/") or not r.content or len(r.content) > max_bytes:
            return None
        return r.content, ctype
    except Exception: return None

def _to_data_uri(raw, ctype):
    try:
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img.thumbnail((500, 500))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        raw, ctype = buf.getvalue(), "image/jpeg"
    except Exception: pass
    return f"data:{ctype};base64," + base64.b64encode(raw).decode()

@st.cache_data(ttl=600, show_spinner=False)
def load_cuneo_site_photos():
    html = _fetch_html(CUNEO_ROSTER_URL)
    photos = {}
    for tag in re.findall(r"<img\b[^>]*>", html, flags=re.I):
        src = _html_attr(tag, ["data-src", "data-lazy-src", "data-original", "src"])
        if not src or "/storage/images/" not in src: continue
        text = " ".join(filter(None, [_html_attr(tag, ["alt"]), _html_attr(tag, ["title"]), src.rsplit("/", 1)[-1]]))
        toks = _tokens(text)
        for surname, full in SURNAME_TO_PLAYER.items():
            if surname in toks and full not in photos:
                photos[full] = urljoin(CUNEO_ROSTER_URL, src)
                break
    return photos

@st.cache_data(ttl=3600, show_spinner=False)
def load_lega_player_ids():
    ids = dict(LEGA_PLAYER_IDS)
    html = _fetch_html(f"{LEGA_BASE}/team/{LEGA_TEAM_ID}")
    for m in re.finditer(r"<a\b[^>]*href=[\"'][^\"']*?/player/([A-Za-z0-9\-]+)[^\"']*[\"'][^>]*>(.*?)</a>", html, flags=re.I | re.S):
        key = m.group(1).upper()
        toks = _tokens(re.sub(r"<[^>]+>", " ", m.group(2)))
        for surname, full in SURNAME_TO_PLAYER.items():
            if surname in toks: ids[full] = key; break
    return ids

@st.cache_data(ttl=600, show_spinner=False)
def get_player_photo(full_name):
    lega_ids = load_lega_player_ids()
    candidates = {
        "cuneo": load_cuneo_site_photos().get(full_name),
        "lega": f"{LEGA_BASE}/Foto.aspx?Key={lega_ids[full_name]}&sqid={LEGA_TEAM_ID}&heightImg=400" if full_name in lega_ids else None
    }
    for source in PHOTO_SOURCE_ORDER:
        url = candidates.get(source)
        if not url: continue
        got = _download_image(url)
        if got: return _to_data_uri(*got)
    return None

def get_custom_week(dt_series):
    days_diff = (dt_series.dt.normalize() - ANCHOR_MONDAY).dt.days
    week_offset = days_diff // 7
    return "Settimana " + (7 + week_offset).astype(int).astype(str)

def extract_week_num(w_str):
    try: return int(w_str.replace("Settimana ", ""))
    except Exception: return 0

def get_csv_files():
    files = glob.glob("data/*.csv") + glob.glob("data/*.CSV") + glob.glob("*.csv") + glob.glob("*.CSV")
    return sorted(set(files))

def get_files_signature():
    sig = []
    for f in get_csv_files():
        try: sig.append((f, os.path.getmtime(f), os.path.getsize(f)))
        except OSError: pass
    return tuple(sig)

@st.cache_data(ttl=60)
def load_jump_data(files_signature):
    files = [s[0] for s in files_signature]
    df_list = []
    for f in files:
        try:
            temp = pd.read_csv(f, sep=";")
            temp.columns = temp.columns.str.strip()
            if "JUMP HEIGHT(cm)" in temp.columns: df_list.append(temp)
        except Exception: pass
    if not df_list: return pd.DataFrame()
    df = pd.concat(df_list, ignore_index=True)
    df.columns = df.columns.str.strip()
    df["JUMP HEIGHT(cm)"] = pd.to_numeric(df["JUMP HEIGHT(cm)"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    df = df.dropna(subset=["JUMP HEIGHT(cm)"]).copy()
    df["ATHLETE"] = df["NAME"].astype(str).str.strip() + " " + df["SURNAME"].astype(str).str.strip()
    df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")
    df["DATE_DT"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df.dropna(subset=["DATE_DT"]).copy()
    time_col = next((c for c in df.columns if c.upper() in TIME_COLUMNS), None)
    date_has_time = ((df["DATE_DT"].dt.hour != 0) | (df["DATE_DT"].dt.minute != 0) | (df["DATE_DT"].dt.second != 0)).any()
    df["DATETIME"] = df["DATE_DT"]
    df["HAS_TIME"] = bool(date_has_time)
    if not date_has_time and time_col is not None:
        combined = pd.to_datetime(df["DATE_DT"].dt.strftime("%Y-%m-%d") + " " + df[time_col].astype(str).str.strip(), errors="coerce")
        if combined.notna().any(): df["DATETIME"] = combined.fillna(df["DATE_DT"]); df["HAS_TIME"] = True
    df["DATE_DT"] = df["DATE_DT"].dt.normalize()
    df["DATE_STR"] = df["DATE_DT"].dt.strftime("%Y-%m-%d")
    df["WEEK"] = get_custom_week(df["DATE_DT"])
    df["IS_MATCH"] = df["DATE_STR"].isin(MATCH_DAYS)
    def classify_jump(h):
        try: val = float(h)
        except Exception: return "Altro"
        if val < 30: return "JUMPS < 30"
        elif 30 <= val <= 50: return "JUMPS 30-50"
        elif 50 < val <= 60: return "JUMPS 50-60"
        elif 60 < val <= 70: return "JUMPS 60-70"
        else: return "JUMPS > 70"
    df["JUMP_BAND"] = df["JUMP HEIGHT(cm)"].apply(classify_jump)
    return df

# ------------------------------------------------------------------------------
# Render principale (Grafica e logica originali)
# ------------------------------------------------------------------------------
def render(allowed_athletes, ruoli_dict_global):
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1: st.markdown("### 🚀 **DataJump** — Monitoraggio Salti & Elevazione")
    with col_h2:
        if st.button("🏠 Torna alla Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

    if allowed_athletes == "ALL": st.sidebar.success("🔓 Visualizzazione: Roster Completo")
    else: st.sidebar.success(f"🔓 Visualizzazione Dedicata: {allowed_athletes[0]}")

    df_jump = load_jump_data(get_files_signature())
    if df_jump.empty:
        st.warning("⚠️ Nessun file CSV relativo ai salti trovato.")
        return

    st.sidebar.caption(f"📁 {len(get_csv_files())} file CSV trovati · {df_jump['DATE_STR'].nunique()} sedute caricate")

    if allowed_athletes != "ALL": df_jump = df_jump[df_jump["ATHLETE"].isin(allowed_athletes)]

    st.sidebar.divider()
    st.sidebar.header("🔍 Filtri Selezione & Confronto")
    ruoli_list = sorted(list(set(df_jump["ROLE"].unique())))
    selected_roles = st.sidebar.multiselect("Filtra per Ruolo", ruoli_list)
    df_f = df_jump.copy()
    if selected_roles: df_f = df_f[df_f["ROLE"].isin(selected_roles)]

    giocatori_list = sorted(df_f["ATHLETE"].unique())
    selected_players = st.sidebar.multiselect("Seleziona Giocatori da Analizzare / Confrontare", giocatori_list)
    if selected_players: df_f = df_f[df_f["ATHLETE"].isin(selected_players)]

    df_base = df_f.copy()

    unique_weeks = sorted([w for w in df_f["WEEK"].unique() if pd.notna(w)], key=extract_week_num, reverse=True)
    selected_weeks = st.sidebar.multiselect("Settimane di Lavoro", unique_weeks)
    if selected_weeks: df_f = df_f[df_f["WEEK"].isin(selected_weeks)]

    sessioni_list = sorted([d for d in df_f["DATE_STR"].unique() if pd.notna(d)], reverse=True)
    selected_sessions = st.sidebar.multiselect("Date Sedute", sessioni_list)
    if selected_sessions: df_f = df_f[df_f["DATE_STR"].isin(selected_sessions)]

    single_player_target = selected_players[0] if selected_players and len(selected_players) == 1 else (allowed_athletes[0] if allowed_athletes != "ALL" else None)

    if single_player_target:
        p = single_player_target
        role_val = ruoli_dict.get(p, "Atleta")
        details = player_info.get(p, {})
        bio_val = details.get("bio", "Cuneo Volley Prima Squadra")
        lega_key = load_lega_player_ids().get(p)
        link_val = f"{LEGA_BASE}/player/{lega_key}" if lega_key else f"{LEGA_BASE}/ricerca/?Search={quote(p.split()[-1])}&TipoOgg=ATL&FindAll=0"

        photo_uri = get_player_photo(p)
        photo_html = f'<img src="{photo_uri}" alt="{html_lib.escape(p)}" style="width:130px;height:130px;object-fit:cover;object-position:top;border-radius:50%;border:3px solid #2563eb;flex-shrink:0;">' if photo_uri else '<div style="font-size:3.2rem;flex-shrink:0;">🛡️</div>'

        card_html = (
            '<div class="player-card" style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">'
            f'{photo_html}<div>'
            f'<div class="player-title">{html_lib.escape(p)}</div>'
            f'<div class="player-role">Ruolo: {html_lib.escape(role_val)}</div>'
            f'<p style="color:#475569;margin-top:8px;margin-bottom:12px;">{html_lib.escape(bio_val)}</p>'
            f'<a href="{link_val}" target="_blank" style="color:#2563eb;text-decoration:none;font-weight:600;">🔗 Vai alla scheda ufficiale su Lega Pallavolo Serie A →</a>'
            '</div></div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    daily_summary = df_f.groupby(["ATHLETE", "ROLE", "DATE_STR", "WEEK"]).agg(
        SALTI_GIORNO=("JUMP HEIGHT(cm)", "count"),
        MAX_GIORNO=("JUMP HEIGHT(cm)", "max"),
        MEDIA_GIORNO=("JUMP HEIGHT(cm)", "mean"),
        IS_MATCH=("IS_MATCH", "max")
    ).reset_index()

    weekly_summary = df_f.groupby(["ATHLETE", "ROLE", "WEEK"]).agg(
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
            if match_dates.empty: chart1 = bars1.properties(height=380)
            else:
                match_bg = alt.Chart(match_dates).mark_rect(color="#f97316", opacity=0.2).encode(
                    x=alt.X("DATE_STR:N", title="Data Seduta"), y=alt.value(0), y2=alt.value(380)
                )
                chart1 = alt.layer(match_bg, bars1).properties(height=380)
            st.altair_chart(chart1, use_container_width=True)
            st.caption("🟠 Colonna / pallino arancione = giorno di partita")

            st.markdown("##### 🚀 Salto Max (cm) — ultime 7 sedute")
            line2 = alt.Chart(daily_recent).mark_line(point=True).encode(
                x=alt.X("DATE_STR:N", title="Data Seduta"),
                y=alt.Y("MAX_GIORNO:Q", title="Salto Max (cm)"),
                color=alt.Color("ATHLETE:N", title="Giocatore"),
                tooltip=["DATE_STR", "ATHLETE", "MAX_GIORNO"]
            )
            match_pts = daily_recent[daily_recent["IS_MATCH"].astype(bool)]
            if match_pts.empty: chart2 = line2.properties(height=380)
            else:
                match_dots = alt.Chart(match_pts).mark_point(filled=True, color="#f97316", size=260).encode(
                    x=alt.X("DATE_STR:N", title="Data Seduta"),
                    y=alt.Y("MAX_GIORNO:Q", title="Salto Max (cm)"),
                    tooltip=["DATE_STR", "ATHLETE", "MAX_GIORNO"]
                )
                chart2 = alt.layer(line2, match_dots).properties(height=380)
            st.altair_chart(chart2, use_container_width=True)

            if single_player_target:
                st.divider()
                st.markdown(f"##### 📈 Andamento dei Salti all'Interno delle Sessioni — {single_player_target}")
                st.info("I grafici seguenti mostrano l'altezza dei singoli salti in ordine cronologico per ciascuna seduta di allenamento dell'atleta, in base all'orario in cui sono stati eseguiti.")
                
                df_session_seq = df_f.copy().sort_values(by=["DATETIME"], kind="stable")
                df_session_seq["NUM_SALTO"] = df_session_seq.groupby(["DATE_STR", "ATHLETE"]).cumcount() + 1
                
                if not df_session_seq.empty and not df_session_seq["HAS_TIME"].any():
                    st.warning("Nei file CSV non trovo l'orario dei salti (né dentro la colonna DATE né in una colonna TIME / ORA / ORARIO / HOUR): sull'asse orizzontale mostro quindi il numero progressivo del salto.")
                
                date_disponibili = sorted(df_session_seq["DATE_STR"].unique(), reverse=True)
                for data_seduta in date_disponibili:
                    df_data_sub = df_session_seq[df_session_seq["DATE_STR"] == data_seduta]
                    has_time = bool(df_data_sub["HAS_TIME"].any())
                    is_match_day = data_seduta in MATCH_DAYS
                    st.markdown(f"**📅 Seduta del: {data_seduta}**" + ("   🟠 **Match day**" if is_match_day else ""))
                    
                    if has_time:
                        x_enc = alt.X("DATETIME:T", title="Orario del salto", axis=alt.Axis(format="%H:%M", labelAngle=0))
                        tooltip_enc = ["ATHLETE", alt.Tooltip("DATETIME:T", title="Orario", format="%H:%M:%S"), alt.Tooltip("NUM_SALTO:Q", title="N° salto"), "JUMP HEIGHT(cm)", "JUMP_BAND"]
                    else:
                        x_enc = alt.X("NUM_SALTO:Q", title="Progressione Salti nella Seduta")
                        tooltip_enc = ["ATHLETE", "NUM_SALTO", "JUMP HEIGHT(cm)", "JUMP_BAND"]
                        
                    chart_intra = alt.Chart(df_data_sub).mark_line(point=True, strokeWidth=2, color="#f97316" if is_match_day else "#2563eb").encode(
                        x=x_enc, y=alt.Y("JUMP HEIGHT(cm):Q", title="Altezza Salto (cm)"), order=alt.Order("NUM_SALTO:Q"), tooltip=tooltip_enc
                    ).properties(height=300, width="container")
                    st.altair_chart(chart_intra, use_container_width=True)

    with tab2:
        if not weekly_summary.empty:
            st.markdown("##### 🔵 Volume Salti Settimanali")
            chart_w = alt.Chart(weekly_summary).mark_bar().encode(
                x=alt.X("WEEK:N", title="Settimana"), y=alt.Y("SALTI_SETTIMANA:Q", title="Nr. Salti"),
                color=alt.Color("ATHLETE:N", title="Giocatore"), tooltip=["WEEK", "ATHLETE", "SALTI_SETTIMANA"]
            ).properties(height=380)
            st.altair_chart(chart_w, use_container_width=True)

    with tab3:
        if not df_f.empty:
            comp_df = df_f.groupby(["ATHLETE", "ROLE"]).agg(
                TOT_SALTI=("JUMP HEIGHT(cm)", "count"), MAX_SALTO=("JUMP HEIGHT(cm)", "max"), MEDIA_SALTO=("JUMP HEIGHT(cm)", "mean")
            ).reset_index()
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Totale Salti per Giocatore**")
                st.altair_chart(alt.Chart(comp_df).mark_bar(color="#2563eb").encode(
                    x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"), y=alt.Y("TOT_SALTI:Q", title="Totale Salti"), tooltip=["ATHLETE", "TOT_SALTI"]
                ).properties(height=350), use_container_width=True)
            with col_b:
                st.write("**Salto Max (cm) per Giocatore**")
                st.altair_chart(alt.Chart(comp_df).mark_bar(color="#f97316").encode(
                    x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"), y=alt.Y("MAX_SALTO:Q", title="Salto Max (cm)"), tooltip=["ATHLETE", "MAX_SALTO"]
                ).properties(height=350), use_container_width=True)

    with tab4:
        if not df_f.empty:
            band_comp = df_f.groupby(["JUMP_BAND", "ATHLETE"]).size().reset_index(name="Numero Salti")
            chart_b = alt.Chart(band_comp).mark_bar().encode(
                x=alt.X("JUMP_BAND:N", sort=BAND_ORDER, title="Fascia"), y=alt.Y("Numero Salti:Q"),
                color=alt.Color("ATHLETE:N", title="Giocatore"), tooltip=["JUMP_BAND", "ATHLETE", "Numero Salti"]
            ).properties(height=400)
            st.altair_chart(chart_b, use_container_width=True)

    with tab5:
        st.markdown("##### 🆚 Confronto tra due settimane di lavoro")
        settimane_cmp = sorted([w for w in df_base["WEEK"].unique() if pd.notna(w)], key=extract_week_num, reverse=True)
        if len(settimane_cmp) < 2: st.info("Servono dati di almeno due settimane per fare il confronto.")
        else:
            col_wa, col_wb = st.columns(2)
            with col_wa: week_a = st.selectbox("Settimana A (riferimento)", settimane_cmp, index=1, key="cmp_week_a")
            with col_wb: week_b = st.selectbox("Settimana B (da confrontare)", settimane_cmp, index=0, key="cmp_week_b")
            
            if week_a == week_b: st.warning("Scegli due settimane diverse per il confronto.")
            else:
                df_a, df_b = df_base[df_base["WEEK"] == week_a], df_base[df_base["WEEK"] == week_b]
                def week_stats(d):
                    if d.empty: return {"salti": 0, "max": 0.0, "media": 0.0, "sedute": 0}
                    h = d["JUMP HEIGHT(cm)"]
                    return {"salti": int(h.count()), "max": float(h.max()), "media": float(h.mean()), "sedute": int(d["DATE_STR"].nunique())}
                sa, sb = week_stats(df_a), week_stats(df_b)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(f"Totale Salti — {week_b}", f"{sb['salti']}", f"{sb['salti'] - sa['salti']:+d} vs {week_a}")
                m2.metric(f"Salto Max — {week_b}", f"{sb['max']:.1f} cm", f"{sb['max'] - sa['max']:+.1f} cm")
                m3.metric(f"Media Salti — {week_b}", f"{sb['media']:.1f} cm", f"{sb['media'] - sa['media']:+.1f} cm")
                m4.metric(f"Sedute — {week_b}", f"{sb['sedute']}", f"{sb['sedute'] - sa['sedute']:+d}")
                
                cmp_df = pd.concat([df_a.assign(SETTIMANA=week_a), df_b.assign(SETTIMANA=week_b)], ignore_index=True)
                cmp_df["GIORNO"] = cmp_df["DATE_DT"].dt.dayofweek.map(lambda i: GIORNI[int(i)])
                cmp_daily = cmp_df.groupby(["SETTIMANA", "GIORNO", "DATE_STR"]).agg(
                    SALTI=("JUMP HEIGHT(cm)", "count"), SALTO_MAX=("JUMP HEIGHT(cm)", "max"),
                    SALTO_MEDIO=("JUMP HEIGHT(cm)", "mean"), IS_MATCH=("IS_MATCH", "max")
                ).reset_index()
                cmp_daily["IS_MATCH"] = cmp_daily["IS_MATCH"].astype(bool)
                week_color = alt.Color("SETTIMANA:N", title="Settimana", scale=alt.Scale(domain=[week_a, week_b], range=["#94a3b8", "#2563eb"]))
                
                def cmp_bar(value_col, title):
                    bars = alt.Chart(cmp_daily).mark_bar().encode(
                        x=alt.X("GIORNO:N", sort=GIORNI, title="Giorno"), xOffset=alt.XOffset("SETTIMANA:N"),
                        y=alt.Y(f"{value_col}:Q", title=title), color=week_color,
                        tooltip=["SETTIMANA", "GIORNO", "DATE_STR", alt.Tooltip("SALTI:Q", title="Salti"), alt.Tooltip("SALTO_MAX:Q", title="Max (cm)", format=".1f"), alt.Tooltip("SALTO_MEDIO:Q", title="Media (cm)", format=".1f")]
                    )
                    match_df = cmp_daily[cmp_daily["IS_MATCH"]]
                    if match_df.empty: return bars.properties(height=340)
                    dots = alt.Chart(match_df).mark_point(filled=True, color="#f97316", size=150).encode(
                        x=alt.X("GIORNO:N", sort=GIORNI), xOffset=alt.XOffset("SETTIMANA:N"), y=f"{value_col}:Q"
                    )
                    return alt.layer(bars, dots).properties(height=340)

                cc1, cc2 = st.columns(2)
                with cc1:
                    st.write("**Volume Salti per Giorno**")
                    st.altair_chart(cmp_bar("SALTI", "Nr. Salti"), use_container_width=True)
                with cc2:
                    st.write("**Salto Max (cm) per Giorno**")
                    st.altair_chart(cmp_bar("SALTO_MAX", "Salto Max (cm)"), use_container_width=True)
                st.caption("🟠 Pallino arancione = giorno di partita")
