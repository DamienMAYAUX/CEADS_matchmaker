# -*- coding: utf-8 -*-
"""Final step of app_assess.py: rate system-proposed candidate matches.

Unlike app_select.py (respondent builds their own counterpart/pair list),
here the app proposes a candidate — a (geography, industry) counterpart for
a provider/consumer, or a (provider, consumer) pair of such for an
intermediary — and the respondent just judges it: a 0-3 rating when
quantity mode is on, or a plain yes/no (recorded as 1/0) when it's off.

The respondent can also ask for a more specific version of the same
candidate: they only say which dimension to narrow — geography or industry
— the system then picks the actual refined value at random (a specific
region, or a specific NACE code), not the respondent.
"""
import random

import streamlit as st
from data import COUNTRY_NAMES, NUTS1, CATS, CAT_NAME, NACE_OPTIONS
from widgets import GEO_OPTIONS, GEO_LABELS, QUANTITY_LABELS, QUANTITY_DOTS, BINARY_DOTS
from schema import build_assessment_payload, download_json_button, build_export_filename

# Chance a proposed candidate has no geography constraint at all ("anywhere").
_ANY_LOCATION_PROB = 0.2


def _random_candidate():
    category = random.choice([cid for cid, _ in CATS])
    geo = [] if random.random() < _ANY_LOCATION_PROB else [random.choice(GEO_OPTIONS)]
    return {"category": category, "category_name": CAT_NAME[category], "geo": geo, "nace": []}


def _nace_label(category, code):
    return dict(NACE_OPTIONS.get(category, [])).get(code, code)


def _describe(candidate):
    geo_txt = ", ".join(GEO_LABELS[g] for g in candidate["geo"]) if candidate["geo"] else "any location"
    if candidate["nace"]:
        nace_txt = ", ".join(f"{c} — {_nace_label(candidate['category'], c)}" for c in candidate["nace"])
        activity_txt = f"{candidate['category']} — {candidate['category_name']} ({nace_txt})"
    else:
        activity_txt = f"{candidate['category']} — {candidate['category_name']}"
    return f"**{activity_txt}**  \n{geo_txt}"


def _new_candidate(role):
    if role == "intermediary":
        return {"provider": _random_candidate(), "consumer": _random_candidate()}
    return _random_candidate()


def _reset_candidate(role):
    st.session_state["candidate"] = _new_candidate(role)
    st.session_state["candidate_seq"] = st.session_state.get("candidate_seq", 0) + 1


def _record(candidate, quantity):
    st.session_state.setdefault("assessments", []).append({"candidate": candidate, "quantity": quantity})
    st.session_state.pop("candidate", None)
    st.rerun()


def _geo_is_whole_country(geo):
    return len(geo) == 1 and geo[0] in COUNTRY_NAMES


def _geo_refinable(geo):
    return not geo or (_geo_is_whole_country(geo) and len(NUTS1.get(geo[0], [])) > 1)


def _nace_refinable(candidate):
    return not candidate["nace"] and bool(NACE_OPTIONS.get(candidate["category"]))


def _refine_geo(candidate):
    """Narrow geography by one step — the system picks the value at random."""
    geo = candidate["geo"]
    if not geo:
        candidate["geo"] = [random.choice(list(COUNTRY_NAMES))]
    elif _geo_is_whole_country(geo):
        regions = NUTS1.get(geo[0], [])
        candidate["geo"] = [random.choice(regions)[0]]


def _refine_nace(candidate):
    """Narrow activity to one NACE code — the system picks the value at random."""
    opts = NACE_OPTIONS.get(candidate["category"], [])
    candidate["nace"] = [random.choice(opts)[0]]


def _render_refine_section(candidate, key_prefix, label):
    geo_refinable = _geo_refinable(candidate["geo"])
    nace_refinable = _nace_refinable(candidate)
    if not (geo_refinable or nace_refinable):
        return
    cols = st.columns(2)
    with cols[0]:
        if geo_refinable:
            if st.button("More specific: geography", key=f"{key_prefix}_geo_refine",
                         type="tertiary", help="The app will pick a specific region at random."):
                _refine_geo(candidate)
                st.rerun()
    with cols[1]:
        if nace_refinable:
            if st.button("More specific: industry", key=f"{key_prefix}_nace_refine",
                         type="tertiary", help="The app will pick a specific NACE code at random."):
                _refine_nace(candidate)
                st.rerun()


def render():
    role = st.session_state.get("role")
    self_profile = st.session_state.get("self_profile")
    if not role or self_profile is None:
        st.warning("Please complete the previous steps first (see the sidebar).")
        st.stop()
    quantity_mode = st.session_state.get("quantity_mode", False)

    st.title("Assess proposed matches")
    st.caption("Rate how likely it is that you are interested in doing data sharing with this counterpart.")

    if "candidate" not in st.session_state:
        _reset_candidate(role)
    candidate = st.session_state["candidate"]
    seq = st.session_state.get("candidate_seq", 0)

    if role == "intermediary":
        st.subheader("Proposed pair")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Provider**")
            st.markdown(_describe(candidate["provider"]))
        with col2:
            st.markdown("**Consumer**")
            st.markdown(_describe(candidate["consumer"]))
        _render_refine_section(candidate["provider"], f"cand{seq}_provider", "provider side")
        _render_refine_section(candidate["consumer"], f"cand{seq}_consumer", "consumer side")
    else:
        other = "consumer" if role == "provider" else "provider"
        st.subheader(f"Proposed {other}")
        st.markdown(_describe(candidate))
        _render_refine_section(candidate, f"cand{seq}", f"proposed {other}")

    st.divider()
    if quantity_mode:
        cols = st.columns(4)
        for col, v in zip(cols, (0, 1, 2, 3)):
            with col:
                if st.button(f"{QUANTITY_DOTS[v]} {v}", key=f"rate_{v}", type="primary",
                              use_container_width=True, help=QUANTITY_LABELS[v]):
                    _record(candidate, v)
    else:
        cols = st.columns(2)
        with cols[0]:
            if st.button(f"{BINARY_DOTS[0]} No potential", type="primary", use_container_width=True):
                _record(candidate, 0)
        with cols[1]:
            if st.button(f"{BINARY_DOTS[1]} Possible match", type="primary", use_container_width=True):
                _record(candidate, 1)

    if st.button("Skip (show another candidate, don't record)"):
        st.session_state.pop("candidate", None)
        st.rerun()

    assessed = st.session_state.get("assessments", [])
    st.divider()
    st.subheader(f"Rated so far ({len(assessed)})")
    if assessed:
        for i, item in enumerate(assessed):
            with st.container(border=True):
                cols = st.columns([5, 3])
                with cols[0]:
                    if role == "intermediary":
                        st.markdown(f"**Provider:** {_describe(item['candidate']['provider'])}")
                        st.markdown(f"**Consumer:** {_describe(item['candidate']['consumer'])}")
                    else:
                        st.markdown(_describe(item["candidate"]))
                with cols[1]:
                    if quantity_mode:
                        picked = st.segmented_control(
                            "Rating", options=[0, 1, 2, 3],
                            format_func=lambda q: f"{QUANTITY_DOTS[q]} {q}",
                            default=item["quantity"], key=f"assessed_{i}_quantity",
                            label_visibility="collapsed",
                        )
                    else:
                        picked = st.segmented_control(
                            "Rating", options=[0, 1],
                            format_func=lambda q: f"{BINARY_DOTS[q]} {'No' if q == 0 else 'Yes'}",
                            default=item["quantity"], key=f"assessed_{i}_quantity",
                            label_visibility="collapsed",
                        )
                    if picked is not None:
                        item["quantity"] = picked

        payload = build_assessment_payload(role, self_profile, assessed)
        download_json_button(payload, filename=build_export_filename("assess"), label="Download assessments (JSON)")
