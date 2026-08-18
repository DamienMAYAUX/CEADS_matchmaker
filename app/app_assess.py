# -*- coding: utf-8 -*-
"""CEADS match assessment — rate system-proposed candidate matches.

Shares Home + Profile steps with app_select.py (see steps/); only the final
step differs. Run:  streamlit run app_assess.py
"""
import streamlit as st
from config import init_session_from_query_params
from steps import home, profile, assess

st.set_page_config(page_title="CEADS match assessment", layout="centered")
init_session_from_query_params()

assess_page = st.Page(assess.render, title="Assess", url_path="assess")
profile_page = st.Page(
    lambda: profile.render(assess_page, next_label="Continue → rate proposed matches"),
    title="Profile", url_path="profile",
)
home_page = st.Page(
    lambda: home.render(profile_page),
    title="Home", url_path="home", default=True,
)

st.navigation([home_page, profile_page, assess_page], position="top").run()
