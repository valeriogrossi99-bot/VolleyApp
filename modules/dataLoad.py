import streamlit as st
import pandas as pd
import altair as alt
import requests
import io
import json
import hmac
import re
import time
import unicodedata
from datetime import date
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

# ------------------------------------------------------------------------------
# Configurazioni e Costanti DataLoad
# ------------------------------------------------------------------------------
SHEET_ID = "1ib2DrRfODly8HT_V8c2PRNdALYt1_vDCAbvtAK7U1aw"
LOG_SHEET_NAME = "Carichi"
SCHEDE_INDEX_SHEET = "Settimane"

LOG_HEADERS_BY_KEY = {
    "DATA": "Data",
    "ATLETA": "Atleta",
    "ESERCIZIO": "Esercizio",
    "PESO": "Peso",
    "REPS": "Reps",
    "RIR": "RIR",
    "BW": "BW",
    "TARGET": "Target",
    "NOTE": "Note",
}
LOG_HEADERS = list(LOG_HEADERS_BY_KEY.values())
ESERCIZI_BASE = ["Back Squat", "Front Squat", "Stacco QB", "Clean"]

LOG_COLUMN_ALIASES = {
    "DATA": ["data", "date", "giorno"],
    "ATLETA": ["atleta", "athlete", "giocatore", "nome"],
    "ESERCIZIO": ["esercizio", "exercise"],
    "PESO": ["peso", "kg", "carico", "peso kg", "peso (kg)", "weight", "weight(kg)", "load"],
    "REPS": ["reps", "ripetizioni", "rip", "ripetizioni (reps)"],
    "RIR": ["rir"],
    "BW": ["bw", "peso corporeo", "body weight", "bodyweight", "pc"],
    "TARGET": ["target", "target xbw", "target x bw", "target (xbw)", "target forza relativa"],
    "NOTE": ["note", "notes"],
}

SESSIONI_LABEL = {
    "A": "A · Forza",
    "B": "B · Forza esplosiva",
    "C": "C · Forza esplosiva",
}

SCHEDA_COLUMN_ALIASES = {
    "EX": ["exercise", "esercizio", "esercizi"],
    "SET": ["set", "serie"],
    "REPS": ["reps", "rep", "ripetizioni"],
    "WEIGHT": ["weight", "peso", "carico", "kg"],
    "RIR": ["rir"],
    "REST": ["rest", "recupero"],
    "NOTE": ["note", "notes"],
}

SCHEDA_META_LABELS = {
    "player": "player", "giocatore": "player", "atleta": "player",
    "role": "role", "ruolo": "role",
    "period": "period", "periodo": "period",
}

REQ_HEADERS = {"User-Agent": "Mozilla/5.0 (Cuneo Volley Performance Hub)"}

cognomi_to_full = {
    "Argilagos": "Bryan Argilagos", "Coscione": "Manuel Coscione",
    "Strehlau": "Alexandre Strehlau", "Champlin": "Ethan Champlin",
    "Giraudo": "Federico Giraudo", "Poriya": "Poriya Khanzadeh",
    "Feral": "Nathan Feral", "Sala": "Lorenzo Sala",
    "Barberio": "Emanuele Barberio", "Mosca": "Leandro Mosca",
    "Codarin": "Lorenzo Codarin", "Volpe": "Nicoló Volpe",
    "Cavaccini": "Mimmo Cavaccini", "Loubeyre": "Thibault Loubeyre",
}

# ------------------------------------------------------------------------------
# Funzioni di utilità
# ------------------------------------------------------------------------------
def _secret(key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default

def _ascii_lower(text):
    text = unicodedata.normalize("NFKD", str(text))
    return text.encode("ascii", "ignore").decode().lower()

def _slug(text):
    return re.sub(r"[^a-z]", "", _ascii_lower(text))

def _tokens(text):
    return {t for t in re.split(r"[^a-z]+", _ascii_lower(text)) if t}

def _to_float(val):
    if pd.isna(val):
        return float("nan")
    s = re.sub(r"[^0-9.\-]", "", str(val).replace(",", "."))
    if s in ("", "-", "."):
        return float("nan")
    try:
        return float(s)
    except Exception:
        return float("nan")

def _resolve_athlete(name, ruoli_dict):
    s = _slug(name)
    if not s:
        return ""
    surname_map = {_slug(n.split()[-1]): n for n in ruoli_dict}
    for surname, full in surname_map.items():
        if s == surname or s.startswith(surname) or s.endswith(surname):
            return full
    return str(name).strip()

def is_admin():
    token = _secret("admin_token")
    given = st.query_params.get("admin", None)
    if isinstance(given, list):
        given = given[0] if given else None
    if not token or not given:
        return False
    return hmac.compare_digest(str(token).strip(), str(given).strip())

def epley_1rm(kg, reps, rir=0):
    reps_eff = float(reps) + max(float(rir or 0), 0.0)
    return float(kg) if reps_eff <= 1 else float(kg) * (1 + reps_eff / 30)

def latest_value(df_src, col):
    if df_src is None or df_src.empty or col not in df_src.columns:
        return None
    s = df_src.dropna(subset=[col]).sort_values("DATE_DT", kind="stable")[col]
    return float(s.iloc[-1]) if len(s) else None

def parse_dates(series):
    s = series.astype(str).str.strip()
    d = pd.to_datetime(s.str.slice(0, 10), format="%Y-%m-%d", errors="coerce")
    m = d.isna()
    if m.any():
        d = d.fillna(pd.to_datetime(s[m], format="%d/%m/%Y", errors="coerce"))
    m = d.isna()
    if m.any():
        d = d.fillna(pd.to_datetime(s[m], errors="coerce", dayfirst=True))
    return d

def has_save_backend():
    return bool(_secret("apps_script_url")) or (_secret("gcp_service_account") is not None or bool(_secret("gcp_service_account_json")))

def append_log_row(values):
    url = _secret("apps_script_url")
    key = _secret("apps_script_key")
    if url:
        if not key:
            raise RuntimeError("Manca apps_script_key nei secrets di Streamlit.")
        r = requests.post(
            str(url).strip(),
            data=json.dumps({"key": str(key), "riga": values}),
            headers={"Content-Type": "text/plain;charset=utf-8"},
            timeout=40,
        )
        res = r.json()
        if not res.get("ok"):
            raise RuntimeError(f"Lo script ha rifiutato il salvataggio: {res.get('errore', 'errore')}")
        return

    import gspread
    raw = _secret("gcp_service_account_json")
    info = json.loads(raw) if raw else dict(_secret("gcp_service_account"))
    if "\\n" in str(info.get("private_key", "")):
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    gc = gspread.service_account_from_dict(info)
    sh = gc.open_by_key(_secret("sheet_id") or SHEET_ID)
    try:
        ws = sh.worksheet(LOG_SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=LOG_SHEET_NAME, rows=2000, cols=len(LOG_HEADERS))
        ws.append_row(LOG_HEADERS, value_input_option="RAW")

    header = ws.row_values(1)
    canon_cols = [next((c for c, al in LOG_COLUMN_ALIASES.items() if str(h).strip().lower() in al), None) for h in header]
    for k, title in LOG_HEADERS_BY_KEY.items():
        if k not in canon_cols:
            header.append(title)
            canon_cols.append(k)
            ws.update_cell(1, len(header), title)
    row = [values.get(c, "") if c else "" for c in canon_cols]
    ws.append_row(row, value_input_option="RAW")

# ------------------------------------------------------------------------------
# Caricamento dati Google Sheets
# ------------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_google_sheet_force(ruoli_dict):
    sheet_id = _secret("sheet_id") or SHEET_ID
    esercizi = ["Back Squat", "Front Squat", "Stacco QB"]
    df_list = []
    for ex in esercizi:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={ex.replace(' ', '%20')}"
            temp = pd.read_csv(url, skiprows=2)
            temp = temp.loc[:, ~temp.columns.str.contains("^Unnamed")]
            temp.columns = temp.columns.astype(str).str.strip()
            if not temp.empty and "Atleta" in temp.columns:
                temp["ESERCIZIO"] = ex
                df_list.append(temp)
        except Exception:
            pass
    if not df_list:
        return pd.DataFrame()
    df = pd.concat(df_list, ignore_index=True)
    df = df[df["Atleta"].notna() & (df["Atleta"] != "Atleta")].copy()

    def clean_num(val):
        if pd.isna(val) or val == "" or val == "-" or "#" in str(val):
            return 0.0
        try:
            return float(str(val).replace(",", ".").strip())
        except Exception:
            return 0.0

    for col in ["BW", "Peso usato", "Reps", "RIR", "1RM Teorico", "1RM/BW", "1RM Ideale"]:
        df[col] = df[col].apply(clean_num) if col in df.columns else 0.0

    df["ATHLETE"] = df["Atleta"].map(cognomi_to_full).fillna(df["Atleta"])
    df["ROLE"] = df["ATHLETE"].map(ruoli_dict).fillna("Altro")
    return df

@st.cache_data(ttl=60)
def load_google_sheet_log(ruoli_dict):
    sheet_id = _secret("sheet_id") or SHEET_ID
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={quote(LOG_SHEET_NAME)}"
    try:
        raw = pd.read_csv(url)
    except Exception:
        return pd.DataFrame()

    rename = {}
    for col in raw.columns:
        key = str(col).strip().lower()
        for canon, aliases in LOG_COLUMN_ALIASES.items():
            if key in aliases and canon not in rename.values():
                rename[col] = canon
                break
    raw = raw.rename(columns=rename)
    if not {"DATA", "ATLETA", "ESERCIZIO", "PESO", "REPS"}.issubset(raw.columns):
        return pd.DataFrame()

    df = raw[[c for c in ["DATA", "ATLETA", "ESERCIZIO", "PESO", "REPS", "RIR", "BW", "TARGET", "NOTE"] if c in raw.columns]].copy()
    for opt in ["RIR", "BW", "TARGET"]:
        if opt not in df.columns:
            df[opt] = float("nan")
    df["NOTE"] = df["NOTE"].fillna("").astype(str) if "NOTE" in df.columns else ""

    for num_col in ["PESO", "REPS", "RIR", "BW", "TARGET"]:
        df[num_col] = df[num_col].apply(_to_float)
    df["BW"] = df["BW"].where(df["BW"] > 0)
    df["TARGET"] = df["TARGET"].where(df["TARGET"] > 0)
    df["DATE_DT"] = parse_dates(df["DATA"])
    df = df.dropna(subset=["DATE_DT", "PESO", "REPS", "ATLETA", "ESERCIZIO"])
    df = df[(df["PESO"] > 0) & (df["REPS"] > 0)].copy()
    if df.empty:
        return pd.DataFrame()

    df["DATE_DT"] = df["DATE_DT"].dt.normalize()
    df["DATE_STR"] = df["DATE_DT"].dt.strftime("%Y-%m-%d")
    df["ATHLETE"] = df["ATLETA"].apply(lambda x: _resolve_athlete(x, ruoli_dict))

    ex_raw = df["ESERCIZIO"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    ex_key = ex_raw.str.lower()
    canon = ex_raw.groupby(ex_key).agg(lambda s: s.value_counts().index[0])
    canon = canon.map(lambda s: s[:1].upper() + s[1:] if s.islower() else s)
    df["ESERCIZIO"] = ex_key.map(canon)

    reps_eff = df["REPS"] + df["RIR"].fillna(0).clip(lower=0)
    e1rm = df["PESO"].where(reps_eff <= 1, df["PESO"] * (1 + reps_eff / 30))
    df["E1RM"] = e1rm.where(reps_eff <= 10)
    df["TONNAGE"] = df["PESO"] * df["REPS"]
    df["SERIE"] = df["PESO"].map(lambda v: f"{v:g}") + " kg × " + df["REPS"].map(lambda v: f"{v:g}")
    return df.reset_index(drop=True)

# ------------------------------------------------------------------------------
# Render Principale Modulo DataLoad
# ------------------------------------------------------------------------------
def render(allowed_athletes, ruoli_dict):
    col_h1, col_h2 = st.columns([8, 2])
    with col_h1:
        st.markdown("### 🏋️‍♂️ **DataLoad** — Carichi, Massimali & Valutazione Forza")
    with col_h2:
        if st.button("🏠 Torna alla Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

    if allowed_athletes == "ALL":
        st.sidebar.success("🔓 Visualizzazione: Roster Completo")
    else:
        st.sidebar.success(f"🔓 Visualizzazione Dedicata: {allowed_athletes[0]}")

    df_force = load_google_sheet_force(ruoli_dict)
    df_log = load_google_sheet_log(ruoli_dict)

    if allowed_athletes != "ALL":
        if not df_force.empty:
            df_force = df_force[df_force["ATHLETE"].isin(allowed_athletes)]
        if not df_log.empty:
            df_log = df_log[df_log["ATHLETE"].isin(allowed_athletes)]

    admin_mode = is_admin()
    if admin_mode:
        st.sidebar.success("✍️ Modalità modifica attiva")

    tab_labels = [
        "📈 Carichi & Massimali (tutti gli esercizi)",
        "🏋️ Valutazione Forza & 1RM (Google Sheet)",
    ]
    if admin_mode:
        all_tabs = st.tabs(["✍️ Inserisci Carichi"] + tab_labels)
        tab_edit, tab_log, tab_force_eval = all_tabs[0], all_tabs[1], all_tabs[2]
    else:
        tab_edit = None
        tab_log, tab_force_eval = st.tabs(tab_labels)

    # --- TAB INSERIMENTO (SOLO ADMIN) -----------------------------------------
    if tab_edit is not None:
        with tab_edit:
            st.markdown("##### ✍️ Inserisci una serie")
            if "edit_flash" in st.session_state:
                st.success(st.session_state.pop("edit_flash"))

            can_save = has_save_backend()
            giocatori_all = sorted(ruoli_dict.keys())
            esercizi_noti = set(ESERCIZI_BASE) | (set(df_log["ESERCIZIO"].unique()) if not df_log.empty else set())

            c1, c2 = st.columns(2)
            with c1:
                e_atleta = st.selectbox("Giocatore", giocatori_all, key="edit_atleta")
            with c2:
                e_scelta = st.selectbox("Esercizio", sorted(esercizi_noti) + ["➕ Nuovo esercizio…"], key="edit_esercizio")
            e_esercizio = st.text_input("Nome del nuovo esercizio", key="edit_nuovo_es").strip() if e_scelta == "➕ Nuovo esercizio…" else e_scelta

            c3, c4, c5, c6 = st.columns(4)
            with c3: e_kg = st.number_input("Kg", 0.0, 600.0, 100.0, 2.5, key="edit_kg")
            with c4: e_reps = st.number_input("Ripetizioni", 1, 30, 5, 1, key="edit_reps")
            with c5: e_rir_sel = st.selectbox("RIR (facoltativo)", ["—", 0, 1, 2, 3, 4, 5], key="edit_rir")
            with c6: e_data = st.date_input("Data", value=date.today(), key="edit_data")

            c7, c8 = st.columns(2)
            with c7: e_bw = st.number_input("Peso corporeo (kg)", 0.0, 250.0, 0.0, 0.5, key="edit_bw")
            with c8: e_target = st.number_input("Target forza relativa (× BW)", 0.0, 10.0, 0.0, 0.05, key="edit_target")
            e_note = st.text_input("Note (facoltativo)", key="edit_note")

            e_rir = None if e_rir_sel == "—" else int(e_rir_sel)
            e1rm_new = epley_1rm(e_kg, e_reps, e_rir or 0)
            st.metric("1RM teorico stimato (Epley)", f"{e1rm_new:.1f} kg")

            if st.button("💾 Salva serie", disabled=not can_save, key="edit_save"):
                if e_esercizio and e_kg > 0:
                    try:
                        append_log_row({
                            "DATA": e_data.strftime("%Y-%m-%d"),
                            "ATLETA": e_atleta,
                            "ESERCIZIO": e_esercizio,
                            "PESO": float(e_kg),
                            "REPS": int(e_reps),
                            "RIR": e_rir if e_rir is not None else "",
                            "BW": float(e_bw) if e_bw > 0 else "",
                            "TARGET": float(e_target) if e_target > 0 else "",
                            "NOTE": e_note.strip(),
                        })
                        load_google_sheet_log.clear()
                        st.session_state["edit_flash"] = f"✅ Salvato: {e_atleta} — {e_esercizio}, {e_kg:g} kg × {e_reps}"
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Errore salvataggio: {exc}")

    # --- TAB CARICHI & MASSIMALI ----------------------------------------------
    with tab_log:
        st.markdown("##### 📈 Carichi, Massimali & Andamento per Esercizio")
        if df_log.empty:
            st.info("ℹ️ Nessun carico registrato per ora nella scheda «Carichi».")
        else:
            atleti_log = sorted(df_log["ATHLETE"].unique())
            sel_atleta = st.selectbox("Atleta", ["Tutti gli atleti"] + atleti_log, key="log_atleta")
            df_l = df_log if sel_atleta == "Tutti gli atleti" else df_log[df_log["ATHLETE"] == sel_atleta]
            esercizi_log = sorted(df_l["ESERCIZIO"].unique())
            sel_es = st.selectbox("Esercizio", esercizi_log, key="log_esercizio")

            rows = []
            for (atl, es), g in df_l.groupby(["ATHLETE", "ESERCIZIO"]):
                g_e = g.dropna(subset=["E1RM"])
                best_e = g_e.loc[g_e["E1RM"].idxmax()] if not g_e.empty else None
                best_w = g.loc[g["PESO"].idxmax()]
                last = g.sort_values("DATE_DT", kind="stable").iloc[-1]
                e1 = float(best_e["E1RM"]) if best_e is not None else None
                rows.append({
                    "Atleta": atl,
                    "Esercizio": es,
                    "1RM stimato (kg)": round(e1, 1) if e1 is not None else None,
                    "Serie del 1RM": best_e["SERIE"] if best_e is not None else "",
                    "Carico max (kg)": float(best_w["PESO"]),
                    "Ultima seduta": last["DATE_STR"],
                    "Ultima serie": last["SERIE"],
                    "Tonnellaggio (kg)": float(round(g["TONNAGE"].sum())),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # Grafico Andamento
            df_t = df_l[df_l["ESERCIZIO"] == sel_es]
            daily_log = df_t.groupby(["ATHLETE", "DATE_STR"]).agg(E1RM=("E1RM", "max"), PESO_MAX=("PESO", "max")).reset_index()
            daily_log["DATA"] = pd.to_datetime(daily_log["DATE_STR"])
            plot_log = daily_log.dropna(subset=["E1RM"])
            if not plot_log.empty:
                chart_tr = alt.Chart(plot_log).mark_line(point=True).encode(
                    x=alt.X("DATA:T", title="Data seduta"),
                    y=alt.Y("E1RM:Q", title="1RM stimato (kg)", scale=alt.Scale(zero=False)),
                    color=alt.Color("ATHLETE:N", title="Atleta"),
                    tooltip=["ATHLETE", "DATE_STR", "E1RM", "PESO_MAX"]
                ).properties(height=360)
                st.altair_chart(chart_tr, use_container_width=True)

    # --- TAB VALUTAZIONE FORZA (FOGLIO GOOGLE) --------------------------------
    with tab_force_eval:
        st.markdown("##### 🏋️‍♂️ Valutazione Forza & Massimali Teorici (Google Drive)")
        if not df_force.empty and "ESERCIZIO" in df_force.columns:
            selected_ex = st.selectbox("Seleziona Esercizio di Forza:", df_force["ESERCIZIO"].unique())
            df_force_sub = df_force[df_force["ESERCIZIO"] == selected_ex]
            cols_to_show = [c for c in ["ATHLETE", "ROLE", "BW", "Peso usato", "Reps", "RIR", "1RM Teorico", "1RM/BW", "1RM Ideale"] if c in df_force_sub.columns]
            st.dataframe(df_force_sub[cols_to_show], use_container_width=True, hide_index=True)
            
            chart_1rm = alt.Chart(df_force_sub).mark_bar(color="#2563eb").encode(
                x=alt.X("ATHLETE:N", sort="-y", title="Giocatore"),
                y=alt.Y("1RM Teorico:Q", title="1RM Teorico (kg)"),
                tooltip=["ATHLETE", "Peso usato", "Reps", "1RM Teorico", "1RM/BW"]
            ).properties(height=360)
            st.altair_chart(chart_1rm, use_container_width=True)
        else:
            st.info("ℹ️ Impossibile caricare il foglio Google di valutazione della forza.")
