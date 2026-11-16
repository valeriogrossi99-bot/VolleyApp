"""app.py — punto di ingresso: avvio, home e smistamento tra le sezioni.

File dell'app (tutti nella stessa cartella):
  app.py       -> questo file (home + routing)
  core.py      -> lingua, grafica, roster atleti, funzioni condivise
  datajump.py  -> sezione DataJump
  dataload.py  -> sezione DataLoad
  pliche.py    -> sezione Pliche Cutanee
"""
from core import *
from datajump import render as render_datajump
from dataload import render as render_dataload
from pliche import render as render_pliche

# Pagina, grafica, lingua, sessione e parametri URL (?atleta=..., ?lang=...)
allowed_athletes = setup_app()

# Controllo automatico dei file CSV (ogni 30 secondi)
watch_data_folder()


# ==============================================================================
# SCHERMATA 1: HOME PAGE
# ==============================================================================
def render_home():
  st.markdown(
      """
        <div class="logo-container">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10" width="140">
        </div>
        <h1 style="text-align: center; font-size: 2.8rem; margin-top: 10px; margin-bottom: 5px;">Cuneo Volley</h1>
        <p style="text-align: center; color: #64748b; font-size: 1.1rem; font-weight: 500; margin-bottom: 30px;">Performance & Analytics Hub</p>
    """,
      unsafe_allow_html=True,
  )

  col_card1, col_card2, col_card3 = st.columns(3)
  with col_card1:
    if st.button(
        "🚀\n\nDataJump\n\nMonitoraggio Salti, Elevazione & Fasce",
        key="btn_jump",
        use_container_width=True,
    ):
      st.session_state.page = "datajump"
      st.rerun()
  with col_card2:
    if st.button(
        "🏋️‍♂️\n\nDataLoad\n\nMonitoraggio Carichi, Massimali & Forza",
        key="btn_load",
        use_container_width=True,
    ):
      st.session_state.page = "dataload"
      st.rerun()
  with col_card3:
    if st.button(
        "📏\n\nPliche Cutanee\n\nPlicometria & Composizione Corporea",
        key="btn_pliche",
        use_container_width=True,
    ):
      st.session_state.page = "pliche"
      st.rerun()


# ==============================================================================
# SMISTAMENTO TRA LE SCHERMATE
# ==============================================================================
if st.session_state.page == "home":
  render_home()
elif st.session_state.page == "datajump":
  render_datajump(allowed_athletes)
elif st.session_state.page == "dataload":
  render_dataload(allowed_athletes)
elif st.session_state.page == "pliche":
  render_pliche(allowed_athletes)

