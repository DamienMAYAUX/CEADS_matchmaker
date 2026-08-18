# -*- coding: utf-8 -*-
"""Geography and activity reference data — both parsed at import time,
from the same kind of source: one expert-knowledge file plus a plain
code -> label CSV.

  Geography: ../nuts_reference.csv (countries + their NUTS-1 regions).
  Activity:  ../sector_specific_expert_knowledge.md (expert knowledge — which
             categories exist, which NACE codes anchor each one, at what
             granularity) plus ../nace_reference.csv (the full NACE Rev. 2
             code -> label list; the authority on which codes are valid).

Both CSVs point to the Eurostat classification they're derived from — see
sector_specific_expert_knowledge.md's "Data sources" section. Nothing here is
hard-coded: edit the .md/.csv files and the app picks it up on next run. Any
NACE code referenced in the .md that isn't in nace_reference.csv is a hard
error at import time (see _load_activity), since that CSV is authoritative.

Public API:
  COUNTRY_NAMES — {country_code: country_name}
  NUTS1         — {country_code: [[nuts1_code, nuts1_name], ...]}
  CATS          — list of (category_id, category_name)
  CAT_NAME      — {category_id: category_name}
  NACE_OPTIONS  — {category_id: [(nace_code, label), ...]}, already expanded
                   to 4-digit for categories whose granularity is "4-digit".
"""
import csv
import os
import re

_ROOT = os.path.join(os.path.dirname(__file__), os.pardir)
_NUTS_CSV_PATH = os.path.join(_ROOT, "nuts_reference.csv")
_NACE_CSV_PATH = os.path.join(_ROOT, "nace_reference.csv")
_CATEGORIES_MD_PATH = os.path.join(_ROOT, "sector_specific_expert_knowledge.md")

_CODE_RE = re.compile(r"`([\d.]+)`")


def _read_csv_rows(path):
    """csv.DictReader over path, skipping '#'-prefixed source-comment lines."""
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


# ---------------------------------------------------------------- geography
def _load_geography():
    country_names = {}
    nuts1 = {}
    for row in _read_csv_rows(_NUTS_CSV_PATH):
        if row["level"] == "country":
            country_names[row["code"]] = row["name"]
        else:
            nuts1.setdefault(row["country_code"], []).append([row["code"], row["name"]])
    return country_names, nuts1


# ------------------------------------------------------------------ activity
# Each category is its own "### C<n> — Name" section; NACE codes are listed
# one per line (optionally nested under a plain-text group heading purely for
# visual structure) rather than crammed into a table cell, so a long list of
# codes stays readable. A section runs until the next heading of any level.
_CATEGORY_HEADING_RE = re.compile(r"^### (C\d+) — (.+?)\s*$", re.MULTILINE)
_ANY_HEADING_RE = re.compile(r"^#{1,6} .*$", re.MULTILINE)
_GRANULARITY_RE = re.compile(r"NACE granularity:\**\s*(\d)-digit", re.IGNORECASE)


def _nace_children(anchor, all_codes):
    """4-digit codes that are a direct child of a 3-digit anchor, e.g.
    "01.11".."01.19" for anchor "01.1" (same prefix, one extra digit)."""
    return sorted(c for c in all_codes if c.startswith(anchor) and len(c) == len(anchor) + 1)


def _load_activity():
    nace_labels = {row["code"]: row["label"] for row in _read_csv_rows(_NACE_CSV_PATH)}

    with open(_CATEGORIES_MD_PATH, encoding="utf-8") as f:
        text = f.read()

    heading_starts = [m.start() for m in _ANY_HEADING_RE.finditer(text)]

    cats = []
    cat_name = {}
    anchors = {}
    granularity = {}
    for m in _CATEGORY_HEADING_RE.finditer(text):
        cid, name = m.group(1), m.group(2).strip()
        chunk_end = next((p for p in heading_starts if p > m.start()), len(text))
        chunk = text[m.end():chunk_end]

        gran_m = _GRANULARITY_RE.search(chunk)
        granularity[cid] = 4 if gran_m and gran_m.group(1) == "4" else 3
        anchors[cid] = _CODE_RE.findall(chunk)

        cats.append((cid, name))
        cat_name[cid] = name

    if not cats:
        raise RuntimeError(
            "sector_specific_expert_knowledge.md: no category sections "
            "(### C<n> — ...) found"
        )

    unknown = [(cid, code) for cid, codes in anchors.items() for code in codes
               if code not in nace_labels]
    if unknown:
        bad = ", ".join(f"{code!r} (category {cid})" for cid, code in unknown)
        raise RuntimeError(
            f"sector_specific_expert_knowledge.md references NACE code(s) not found "
            f"in nace_reference.csv, the authority for valid codes: {bad}"
        )

    nace_options = {}
    for cid, anchor_codes in anchors.items():
        codes = []
        seen = set()
        for code in anchor_codes:
            if granularity[cid] == 4:
                children = _nace_children(code, nace_labels)
                expansion = children if children else [code]
            else:
                expansion = [code]
            for c in expansion:
                # A group and its children can both be listed (for visual
                # structure); de-duplicate rather than offer a code twice.
                if c not in seen:
                    seen.add(c)
                    codes.append(c)
        nace_options[cid] = [(code, nace_labels[code]) for code in codes]

    return cats, cat_name, nace_options


COUNTRY_NAMES, NUTS1 = _load_geography()
CATS, CAT_NAME, NACE_OPTIONS = _load_activity()
