# -*- coding: utf-8 -*-
"""Step 1 (shared): choose your role.

Used as-is by both app_select.py (build your own counterpart list) and
app_assess.py (rate system-proposed candidates) — no duplication, the
entry-point script just tells this step which page to link to next.
"""
import streamlit as st

ROLE_LABELS = {
    "provider": "Data provider — I own or store data and I can make it accessible",
    "consumer": "Data consumer — I need or use data",
    "intermediary": "Data intermediary — I connect data providers and data consumers",
}


def render(next_page):
    st.title("Data-Sharing Matchmaker")
    st.caption("Mapping the potential for agricultural data-sharing across Europe.")

    st.header("Who are you?")
    role = st.radio(
        "Select your role",
        options=list(ROLE_LABELS),
        format_func=lambda r: ROLE_LABELS[r],
        index=None,
        key="role_choice",
    )

    if role:
        st.session_state["role"] = role
        st.page_link(next_page, label="Continue", icon="➡️")
