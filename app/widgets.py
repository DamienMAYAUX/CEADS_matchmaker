# -*- coding: utf-8 -*-
"""Reusable Streamlit widgets shared across pages."""
import streamlit as st
from data import COUNTRY_NAMES, NUTS1, CATS, CAT_NAME, NACE_OPTIONS

# Business-value quantity scale (used only when "quantity mode" is on).
QUANTITY_LABELS = {
    0: "0 — No potential: this pairing will almost never want to share data with each other.",
    1: "1 — Limited: a match happens occasionally or value created is modest when it does.",
    2: "2 — Meaningful: a match is fairly likely and it would create solid business value.",
    3: "3 — Near-systematic: this pairing almost always represents a genuine business "
       "interest, with high potential for value creation.",
}
QUANTITY_GUIDANCE = (
    "Rate both how *likely* a match is and how much *value* it would create if it "
    "happened. 0 = no potential at all, "
    "3 = near-systematic match with high value creation."
)
DEFAULT_QUANTITY = 1

# Color-coded dots, low to high potential — lets a 0-3 (or 0/1) rating be read
# at a glance instead of as a bare number.
QUANTITY_DOTS = {0: "⚪", 1: "🟡", 2: "🟠", 3: "🟢"}
BINARY_DOTS = {0: "⚪", 1: "🟢"}


def quantity_badge(quantity, quantity_mode):
    """Small colored badge for a quantity value, for use in list displays."""
    if not quantity_mode:
        return ""
    return f"{QUANTITY_DOTS[quantity]} {quantity}"


def pick_quantity(key_prefix, quantity_mode, label="Business-value potential"):
    """Return a 0-3 quantity rating when quantity_mode is on, else the fixed default (1)."""
    if not quantity_mode:
        return DEFAULT_QUANTITY
    picked = st.segmented_control(
        label,
        options=[0, 1, 2, 3],
        format_func=lambda q: f"{QUANTITY_DOTS[q]} {q}",
        default=DEFAULT_QUANTITY,
        help=QUANTITY_GUIDANCE,
        key=f"{key_prefix}_quantity",
    )
    return DEFAULT_QUANTITY if picked is None else picked


# ---------------------------------------------------------------- geography
# One combined list of options — whole countries and their NUTS-1 regions —
# so a single field can express either "anywhere in France" (pick "FR") or
# "just this region" (pick "FR1") without a separate country-then-region step.
# Public so other modules (e.g. the assess step's random-candidate generator)
# can reuse the same pool instead of rebuilding it.
GEO_OPTIONS = []
GEO_LABELS = {}
for _c in sorted(COUNTRY_NAMES, key=lambda c: COUNTRY_NAMES[c]):
    GEO_OPTIONS.append(_c)
    GEO_LABELS[_c] = f"{_c} — {COUNTRY_NAMES[_c]}"
    for _code, _name in NUTS1.get(_c, []):
        GEO_OPTIONS.append(_code)
        GEO_LABELS[_code] = f"{_code} — {_name} ({COUNTRY_NAMES[_c]})"


def location_to_country_nuts(code):
    if code in COUNTRY_NAMES:
        return code, []
    return code[:2], [code]


def pick_country(key_prefix, label="Country", default_country=None):
    """Plain country picker, no region refinement. Returns the country code or None."""
    state_key = f"{key_prefix}_country"
    if default_country in COUNTRY_NAMES and state_key not in st.session_state:
        st.session_state[state_key] = default_country
    return st.selectbox(
        label,
        options=sorted(COUNTRY_NAMES, key=lambda c: COUNTRY_NAMES[c]),
        format_func=lambda c: f"{c} — {COUNTRY_NAMES[c]}",
        index=None,
        placeholder="Select a country",
        key=state_key,
    )


def pick_location(key_prefix, label="Country / region", default_country=None):
    """Single combined country-or-region picker. Returns (country, [nuts1_code]).

    One field: pick a plain country for "anywhere in that country", or a
    specific NUTS-1 region within it for more precision — no second widget.
    default_country pre-selects that country (whole-country) the first time
    the widget is rendered.
    """
    state_key = f"{key_prefix}_location"
    if default_country in COUNTRY_NAMES and state_key not in st.session_state:
        st.session_state[state_key] = default_country
    picked = st.selectbox(
        label,
        options=GEO_OPTIONS,
        format_func=lambda code: GEO_LABELS[code],
        index=None,
        placeholder="Select a country, or a specific region for more precision",
        key=state_key,
    )
    if not picked:
        return None, []
    return location_to_country_nuts(picked)


def pick_locations_multi(key_prefix, label="Country / region(s)"):
    """Multi combined country-or-region picker. Returns a list of mixed codes
    (bare country codes and/or NUTS-1 codes) — [] means any location."""
    return st.multiselect(
        label,
        options=GEO_OPTIONS,
        format_func=lambda code: GEO_LABELS[code],
        key=f"{key_prefix}_locations",
    )


# ---------------------------------------------------------------- activity
def pick_single_category_activity(key_prefix):
    """Single category + multi NACE picker. Returns (category, [nace_codes])."""
    category = st.selectbox(
        "Activity category",
        options=[cid for cid, _ in CATS],
        format_func=lambda cid: f"{cid} — {CAT_NAME[cid]}",
        index=None,
        placeholder="Select a category",
        key=f"{key_prefix}_category",
    )
    nace = []
    if category:
        opts = NACE_OPTIONS.get(category, [])
        labels = {code: f"{code} — {lab}" for code, lab in opts}
        nace = st.multiselect(
            "NACE group(s) *(leave empty = any activity in this category)*",
            options=[code for code, _ in opts],
            format_func=lambda code: labels[code],
            key=f"{key_prefix}_nace",
        )

    return category, nace


def pick_multi_category_activities(key_prefix):
    """Multi-category activity picker, for a self profile that may span several
    activities. Returns a list of dicts: {category, category_name, nace:[...]}."""
    picked = st.multiselect(
        "Activity categories",
        options=[cid for cid, _ in CATS],
        format_func=lambda cid: f"{cid} — {CAT_NAME[cid]}",
        key=f"{key_prefix}_categories",
    )

    results = []
    for cid in picked:
        with st.expander(f"{cid} — {CAT_NAME[cid]}", expanded=True):
            opts = NACE_OPTIONS.get(cid, [])
            labels = {code: f"{code} — {lab}" for code, lab in opts}
            nace_sel = st.multiselect(
                "NACE group(s) *(leave empty = any activity in this category)*",
                options=[code for code, _ in opts],
                format_func=lambda code: labels[code],
                key=f"{key_prefix}_{cid}_nace",
            )
            results.append({"category": cid, "category_name": CAT_NAME[cid], "nace": nace_sel})
    return results


def pick_counterparts(key_prefix, quantity_mode=False):
    """Multi-category counterpart picker (category + geo + NACE per category).

    Returns a list of dicts: {category, category_name, geo:[...], nace:[...], quantity}.
    quantity is always 1 unless quantity_mode is on, in which case it's a 0-3
    rating of business-value potential for that category.
    """
    picked = st.multiselect(
        "Select the categories you are interested in",
        options=[cid for cid, _ in CATS],
        format_func=lambda cid: f"{cid} — {CAT_NAME[cid]}",
        key=f"{key_prefix}_cats",
    )

    results = []
    for cid in picked:
        with st.expander(f"{cid} — {CAT_NAME[cid]}", expanded=True):
            geo_codes = pick_locations_multi(
                f"{key_prefix}_{cid}",
                label="Geography *(leave empty = any country)*",
            )

            st.markdown("**Activity (NACE)** *(leave empty = any activity)*")
            opts = NACE_OPTIONS.get(cid, [])
            if opts:
                labels = {code: f"{code} — {lab}" for code, lab in opts}
                nace_sel = st.multiselect(
                    "NACE group(s)",
                    options=[code for code, _ in opts],
                    format_func=lambda code: labels[code],
                    key=f"{key_prefix}_{cid}_nace",
                )
            else:
                st.info("No NACE refinement for this category (data-space initiative).")
                nace_sel = []

            quantity = pick_quantity(f"{key_prefix}_{cid}", quantity_mode)

            results.append({"category": cid, "category_name": CAT_NAME[cid],
                             "geo": geo_codes, "nace": nace_sel, "quantity": quantity})
    return results
