# -*- coding: utf-8 -*-
"""Final step of app_select.py: build your own list of counterparts / pairs."""
import streamlit as st
from widgets import (pick_counterparts, pick_location, pick_single_category_activity,
                      pick_quantity, quantity_badge)
from schema import (build_payload, download_json_button, build_export_filename,
                     party_dict, pair_dict, csv_template_bytes, parse_pairs_csv)


def render():
    quantity_mode = st.session_state.get("quantity_mode", False)
    role = st.session_state.get("role")
    self_profile = st.session_state.get("self_profile")
    if not role or self_profile is None:
        st.warning("Please complete the previous steps first (see the sidebar).")
        st.stop()

    st.title("Matching")

    # ------------------------------------------------------------ provider / consumer
    if role in ("provider", "consumer"):
        other = "data consumers" if role == "provider" else "data providers"
        st.header(f"Which {other} are you interested in the context of data-sharing?")
        counterparts = pick_counterparts("match", quantity_mode=quantity_mode)

        if counterparts:
            payload = build_payload(role, self_profile, counterparts=counterparts)
            st.header("Your list")
            for r in counterparts:
                parts = []
                if r["nace"]:
                    parts.append("NACE " + ", ".join(r["nace"]))
                if r["geo"]:
                    parts.append(", ".join(r["geo"]))
                suffix = f" [{' · '.join(parts)}]" if parts else ""
                badge = quantity_badge(r["quantity"], quantity_mode)
                prefix = f"{badge}  " if badge else ""
                st.markdown(f"- {prefix}{r['category']} {r['category_name']}{suffix}")

            download_json_button(payload, filename=build_export_filename("select"))
        else:
            st.info(f"Select at least one category of {other} above.")

    # ------------------------------------------------------------ intermediary
    else:
        st.header("Provider ↔ consumer pairs you believe are a good match")
        st.caption(
            "Build the list one pair at a time, or import a CSV — both feed "
            "the same running list below."
        )

        if "pairs" not in st.session_state:
            st.session_state["pairs"] = []

        tab_manual, tab_csv = st.tabs(["✍️ Add pairs manually", "📄 Import from CSV"])

        with tab_manual:
            own_country = self_profile.get("country")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Provider")
                p_country, p_nuts = pick_location(
                    "pair_provider", label="Provider country / region", default_country=own_country)
                p_category, p_nace = pick_single_category_activity("pair_provider")
            with col2:
                st.subheader("Consumer")
                c_country, c_nuts = pick_location(
                    "pair_consumer", label="Consumer country / region", default_country=own_country)
                c_category, c_nace = pick_single_category_activity("pair_consumer")

            pair_quantity = pick_quantity("pair", quantity_mode)

            can_add = p_country and p_category and c_country and c_category
            if st.button("Add pair", type="primary", use_container_width=True, disabled=not can_add):
                st.session_state["pairs"].append(pair_dict(
                    party_dict(p_country, p_nuts, p_category, p_nace),
                    party_dict(c_country, c_nuts, c_category, c_nace),
                    quantity=pair_quantity,
                ))
                st.rerun()
            if not can_add:
                st.caption("Select at least a country and category for both provider and consumer.")

        with tab_csv:
            quantity_col_note = (
                "- `quantity` *(optional)*: 0-3 business-value rating (see the scale above); "
                "only used when quantity mode is on, otherwise ignored.\n"
                if quantity_mode else
                "- `quantity` *(optional)*: ignored while quantity mode is off — every imported pair gets 1.\n"
            )
            st.markdown(
                "Columns: `provider_country, provider_nuts1, provider_category, provider_nace, "
                "consumer_country, consumer_nuts1, consumer_category, consumer_nace, quantity`.\n\n"
                "- `provider_country` / `consumer_country`: 2-letter country code (e.g. `FR`).\n"
                "- `*_nuts1`: NUTS-1 code(s), separated by `;` if several; leave blank for whole country.\n"
                "- `*_category`: category code (e.g. `C1`); required.\n"
                "- `*_nace`: NACE code(s), separated by `;` if several; leave blank for any activity.\n"
                + quantity_col_note
            )
            st.download_button(
                "Download CSV template",
                data=csv_template_bytes(),
                file_name="ceads_pairs_template.csv",
                mime="text/csv",
            )
            uploaded = st.file_uploader("Upload filled-in CSV", type=["csv"])
            if uploaded is not None:
                try:
                    imported = parse_pairs_csv(uploaded, quantity_mode=quantity_mode)
                except ValueError as e:
                    st.error(str(e))
                else:
                    if st.button(f"Add {len(imported)} pair(s) from CSV", type="primary"):
                        st.session_state["pairs"].extend(imported)
                        st.rerun()

        st.subheader(f"Current pairs ({len(st.session_state['pairs'])})")
        if st.session_state["pairs"]:
            for i, pair in enumerate(st.session_state["pairs"]):
                p, c = pair["provider"], pair["consumer"]
                badge = quantity_badge(pair.get("quantity", 1), quantity_mode)
                prefix = f"{badge}  " if badge else ""
                cols = st.columns([8, 1])
                with cols[0]:
                    st.markdown(
                        f"**{i+1}.** {prefix}Provider: {p['category']} {p['category_name']} "
                        f"({p['country']}{' ' + ','.join(p['nuts1']) if p['nuts1'] else ''}"
                        f"{' · NACE ' + ','.join(p['nace']) if p['nace'] else ''}) "
                        f"→ Consumer: {c['category']} {c['category_name']} "
                        f"({c['country']}{' ' + ','.join(c['nuts1']) if c['nuts1'] else ''}"
                        f"{' · NACE ' + ','.join(c['nace']) if c['nace'] else ''})"
                    )
                with cols[1]:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state["pairs"].pop(i)
                        st.rerun()

            payload = build_payload(role, self_profile, pairs=st.session_state["pairs"])
            download_json_button(payload, filename=build_export_filename("select"))
        else:
            st.info("Add at least one pair (manually or via CSV) to continue.")
