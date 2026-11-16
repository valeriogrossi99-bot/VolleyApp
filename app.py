import streamlit as st
from modules import datajump, dataload, pliche

st.set_page_config(
    page_title="Cuneo Volley Performance Hub",
    page_icon="🏐",
    layout="wide"
)

if "page" not in st.session_state:
    st.session_state.page = "home"

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

def get_allowed_athletes():
    import hmac
    admin_token = st.secrets.get("admin_token", "")
    given = st.query_params.get("admin", None)
    if isinstance(given, list):
        given = given[0] if given else None
    if admin_token and given and hmac.compare_digest(str(admin_token).strip(), str(given).strip()):
        return "ALL"
    atleta_param = st.query_params.get("atleta", None)
    if isinstance(atleta_param, list):
        atleta_param = atleta_param[0] if atleta_param else None
    if atleta_param and atleta_param in ruoli_dict:
        return [atleta_param]
    return "ALL"

allowed_athletes = get_allowed_athletes()

# Router pagine
if st.session_state.page == "home":
    st.title("🏐 Cuneo Volley Performance Hub")
    st.markdown("Benvenuto nel sistema di monitoraggio della performance.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 DataJump", use_container_width=True):
            st.session_state.page = "datajump"
            st.rerun()
    with col2:
        if st.button("🏋️‍♂️ DataLoad", use_container_width=True):
            st.session_state.page = "dataload"
            st.rerun()
    with col3:
        if st.button("📊 Pliche & Composizione", use_container_width=True):
            st.session_state.page = "pliche"
            st.rerun()

elif st.session_state.page == "datajump":
    datajump.render(allowed_athletes, ruoli_dict)

elif st.session_state.page == "dataload":
    dataload.render(allowed_athletes, ruoli_dict)

elif st.session_state.page == "pliche":
    pliche.render(allowed_athletes, ruoli_dict)
