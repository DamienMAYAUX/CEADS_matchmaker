# -*- coding: utf-8 -*-
"""Feature flags for a given data-collection wave.

Not exposed as an in-app UI control, so respondents can't see or flip it
mid-session — but overridable per deployment link via the `binary_value`
URL query parameter (see init_session_from_query_params below), so a
coordinator can hand different respondents different links without
touching the code.
"""
import streamlit as st

# Fallback used when the URL has no (valid) ?binary_value= override.
# When True: matches/pairs (app_select.py) and assessments (app_assess.py)
# are rated on the 0-3 business-value scale (see widgets.QUANTITY_LABELS).
# When False: app_select.py silently records quantity 1 for everything, and
# app_assess.py asks a plain yes/no instead (recorded as 1/0).
QUANTITY_MODE = False


def init_session_from_query_params():
    """Read ?organization_name= and ?binary_value= from the URL, if present,
    and store them in session state for the rest of the app to use.

    Streamlit's internal page navigation (e.g. Home -> Profile -> Match) can
    drop the query string from the URL on later reruns, so a param that's
    missing on a given rerun does NOT reset what was already captured —
    it's only ever set once, the first time it's seen.

    - organization_name: plain string, used to name the exported JSON file.
    - binary_value: "1" -> binary rating (two values, 0/1); "0" -> the
      0-3 quantity scale (four values). Falls back to QUANTITY_MODE above
      when never seen as "0"/"1".
    """
    org = st.query_params.get("organization_name")
    if org:
        st.session_state["organization_name"] = org
    else:
        st.session_state.setdefault("organization_name", "")

    raw = st.query_params.get("binary_value")
    if raw == "0":
        st.session_state["quantity_mode"] = True
    elif raw == "1":
        st.session_state["quantity_mode"] = False
    else:
        st.session_state.setdefault("quantity_mode", QUANTITY_MODE)
