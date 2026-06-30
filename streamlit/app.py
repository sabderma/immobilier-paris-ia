from __future__ import annotations

# Point d'entree Streamlit de l'interface developpee pour C17.

import streamlit as st


st.set_page_config(
    page_title="Immobilier Paris",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from frontend.application import main


if __name__ == "__main__":
    main()
