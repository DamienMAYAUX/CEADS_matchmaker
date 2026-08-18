# -*- coding: utf-8 -*-
"""Unified output schema + CSV import/export helpers for the intermediary pair flow.

Every mode (provider / consumer / intermediary) ends up producing the same
top-level JSON shape:

{
  "role": "provider" | "consumer" | "intermediary",
  "self_profile": {"country": .., "nuts1": [..], "activities": [{"category":.., "category_name":.., "nace":[..]}, ...]}
                   | {"country": ..},  # country-only for intermediary
  "counterparts": [{"category":.., "category_name":.., "geo":[..], "nace":[..], "quantity":..}, ...],
  "pairs": [{"provider": {...party...}, "consumer": {...party...}, "quantity":..}, ...]
}

"self_profile.nuts1" holds at most one NUTS-1 code, since geography is now a
single combined "country or region" field (see widgets.pick_location):
picking a country means [], picking a region means [that_region_code].

"counterparts" is used by provider/consumer modes, "pairs" by intermediary mode;
the unused one is always present as an empty list so downstream tooling can rely
on a fixed schema.

"quantity" is a 0-3 rating of business-value potential, collected only when
"quantity mode" is toggled on; otherwise it defaults to 1 for every entry.
"""
import csv
import datetime
import io
import json
import re

import streamlit as st
from data import CAT_NAME

CSV_COLUMNS = [
    "provider_country", "provider_nuts1", "provider_category", "provider_nace",
    "consumer_country", "consumer_nuts1", "consumer_category", "consumer_nace",
]
CSV_OPTIONAL_COLUMNS = ["quantity"]
DEFAULT_QUANTITY = 1


def build_payload(role, self_profile, counterparts=None, pairs=None):
    return {
        "role": role,
        "self_profile": self_profile,
        "counterparts": counterparts or [],
        "pairs": pairs or [],
    }


def build_assessment_payload(role, self_profile, assessments):
    """Output shape for app_assess.py — rated system-proposed candidates.

    {
      "role": ..., "self_profile": ...,
      "assessments": [{"candidate": <Counterpart-shaped dict> | {"provider":.., "consumer":..},
                        "quantity": 0-3 or 0/1}, ...]
    }

    "candidate" is a single {category, category_name, geo, nace} dict for
    provider/consumer roles, or a {"provider": party, "consumer": party}
    pair for intermediaries — mirroring "Counterpart" and "Pair" from
    build_payload, just system-proposed instead of user-picked.
    """
    return {
        "role": role,
        "self_profile": self_profile,
        "assessments": assessments,
    }


def build_export_filename(app_name):
    """Export filename: <app_name>_<organization_name>_<timestamp>.json.

    app_name is "select" or "assess". organization_name comes from the
    ?organization_name= URL query param (see config.init_session_from_query_params),
    falling back to "unspecified" when absent; non-filename-safe characters
    are stripped. Timestamp reflects the moment the download button is
    rendered.
    """
    org = re.sub(r"[^A-Za-z0-9_-]+", "_", st.session_state.get("organization_name") or "").strip("_")
    org = org or "unspecified"
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{app_name}_{org}_{timestamp}.json"


def download_json_button(payload, filename="ceads_selection.json", label="Download selection (JSON)"):
    st.download_button(
        label,
        data=json.dumps(payload, ensure_ascii=False, indent=2),
        file_name=filename,
        mime="application/json",
    )


def party_dict(country, nuts1, category, nace):
    """Build a {country, nuts1, category, nace} party dict for a pair."""
    return {
        "country": country,
        "nuts1": list(nuts1) if nuts1 else [],
        "category": category,
        "category_name": CAT_NAME.get(category, ""),
        "nace": list(nace) if nace else [],
    }


def pair_dict(provider, consumer, quantity=DEFAULT_QUANTITY):
    """Build a {provider, consumer, quantity} pair dict from two party dicts."""
    return {"provider": provider, "consumer": consumer, "quantity": quantity}


def csv_template_bytes():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_COLUMNS + CSV_OPTIONAL_COLUMNS)
    writer.writerow(["FR", "FRI", "C1", "01.1;01.2", "DE", "DE1", "C4", "10.1", "2"])
    return buf.getvalue().encode("utf-8")


def parse_pairs_csv(uploaded_file, quantity_mode=False):
    """Parse an uploaded CSV file-like object into a list of pair dicts.

    Missing/blank nuts1 or nace fields mean "indifferent" (empty list).
    Multiple codes within a cell are separated by ';'.
    An optional "quantity" column (0-3) is honoured only when quantity_mode
    is on; otherwise every imported pair gets the default quantity (1).
    Raises ValueError with a human-readable message on malformed rows.
    """
    text = uploaded_file.getvalue().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")
    has_quantity_col = "quantity" in (reader.fieldnames or [])

    def split(cell):
        cell = (cell or "").strip()
        return [x.strip() for x in cell.split(";") if x.strip()]

    pairs = []
    for i, row in enumerate(reader, start=2):  # header is row 1
        provider_country = (row["provider_country"] or "").strip()
        consumer_country = (row["consumer_country"] or "").strip()
        provider_category = (row["provider_category"] or "").strip()
        consumer_category = (row["consumer_category"] or "").strip()
        if not provider_country or not consumer_country:
            raise ValueError(f"Row {i}: provider_country and consumer_country are required.")
        if not provider_category or not consumer_category:
            raise ValueError(f"Row {i}: provider_category and consumer_category are required.")

        quantity = DEFAULT_QUANTITY
        if quantity_mode and has_quantity_col:
            raw = (row.get("quantity") or "").strip()
            if raw:
                try:
                    quantity = int(raw)
                except ValueError:
                    raise ValueError(f"Row {i}: quantity must be an integer between 0 and 3, got {raw!r}.")
                if quantity not in (0, 1, 2, 3):
                    raise ValueError(f"Row {i}: quantity must be between 0 and 3, got {quantity}.")

        pairs.append(pair_dict(
            party_dict(provider_country, split(row["provider_nuts1"]),
                       provider_category, split(row["provider_nace"])),
            party_dict(consumer_country, split(row["consumer_nuts1"]),
                       consumer_category, split(row["consumer_nace"])),
            quantity=quantity,
        ))
    return pairs
