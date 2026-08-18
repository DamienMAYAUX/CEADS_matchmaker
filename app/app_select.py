# -*- coding: utf-8 -*-
"""CEADS counterpart selector — build your own list of counterparts / pairs.

Shares Home + Profile steps with app_assess.py (see steps/); only the final
step differs. Run:  streamlit run app_select.py
"""
import streamlit as st
from config import init_session_from_query_params
from steps import home, profile, select_match

st.set_page_config(page_title="CEADS counterpart selector", layout="centered")
init_session_from_query_params()

match_page = st.Page(select_match.render, title="Match", url_path="match")
profile_page = st.Page(
    lambda: profile.render(match_page, next_label="Continue → select counterparts"),
    title="Profile", url_path="profile",
)
home_page = st.Page(
    lambda: home.render(profile_page),
    title="Home", url_path="home", default=True,
)

st.navigation([home_page, profile_page, match_page], position="top").run()
