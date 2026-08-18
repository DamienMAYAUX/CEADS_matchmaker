# -*- coding: utf-8 -*-
"""Step 2 (shared): describe yourself (self profile).

Used as-is by both app_select.py and app_assess.py.
"""
import streamlit as st
from widgets import pick_country, pick_location, pick_multi_category_activities

ROLE_LABELS = {
    "provider": "Data provider",
    "consumer": "Data consumer",
    "intermediary": "Data intermediary",
}


def render(next_page, next_label="Continue"):
    """next_label lets each app phrase the forward link in its own terms
    (e.g. "select counterparts" vs "rate proposed matches")."""
    role = st.session_state.get("role")
    if not role:
        st.warning("Please select your role on the Home page first (see the sidebar).")
        st.stop()

    st.title("Your profile")
    st.caption(f"Role: **{ROLE_LABELS[role]}**")

    if role == "intermediary":
        st.header("Where are you based?")
        country = pick_country("self", label="Country")
        if country:
            st.session_state["self_profile"] = {"country": country}
            st.page_link(next_page, label=next_label, icon="➡️")

    else:
        st.header("Where are you based?")
        country, nuts1 = pick_location("self", label="Country / region")

        st.header("What is your activity?")
        activities = pick_multi_category_activities("self")

        if country and activities:
            st.session_state["self_profile"] = {
                "country": country,
                "nuts1": nuts1,
                "activities": activities,
            }
            st.page_link(next_page, label=next_label, icon="➡️")
        else:
            st.caption("Select at least your country/region and one activity category to continue.")
