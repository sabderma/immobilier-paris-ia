from __future__ import annotations

import streamlit as st


st.set_page_config(
    page_title="Immobilier paris",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from frontend.application import main


if __name__ == "__main__":
    main()
