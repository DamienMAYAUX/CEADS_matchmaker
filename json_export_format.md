# CEADS counterpart-selector — output JSON format

This document specifies the JSON produced by the two `app`
Streamlit apps:

- **`app_select.py`** ("Home" → "Profile" → "Match"): the respondent builds
  their own list of desired counterparts / pairs. Output: `role`,
  `self_profile`, `counterparts`, `pairs` (this document's main subject).
- **`app_assess.py`** ("Home" → "Profile" → "Assess"): the app proposes
  candidate matches (a counterpart, or a provider/consumer pair) and the
  respondent rates each one. Output: `role`, `self_profile`, `assessments`
  (see [Assessment output](#assessment-output-appassesspy) near the end).

The two apps share the "Home" and "Profile" steps (`steps/home.py`,
`steps/profile.py`) and every helper module — there is no duplicated code,
just a different final step (`steps/select_match.py` vs `steps/assess.py`).
`self_profile`'s shape, described below, is identical in both apps.

**Scope**: this document is a technical specification of the JSON *shape* —
field names, types, nesting — for programmers and AI models consuming the
output. It intentionally says nothing about what the category/NACE/geography
*values* mean or where they come from; that's expert-knowledge content, kept
in [`sector_specific_expert_knowledge.md`](sector_specific_expert_knowledge.md),
[`nace_reference.csv`](nace_reference.csv) and
[`nuts_reference.csv`](nuts_reference.csv) instead.

Every `app_select.py` session — regardless of role — outputs **one JSON
object with the same four top-level keys**. Unused sections are present as
empty arrays/objects rather than omitted, so downstream tooling can rely on
a fixed shape.

## Top-level structure

```json
{
  "role": "provider | consumer | intermediary",
  "self_profile": { ... },
  "counterparts": [ ... ],
  "pairs": [ ... ]
}
```

| Field | Type | Meaning |
|---|---|---|
| `role` | string enum | Which of the three modes produced this record. One of `"provider"`, `"consumer"`, `"intermediary"`. |
| `self_profile` | object | Who is submitting the record. Shape depends on `role` (see below). |
| `counterparts` | array of `Counterpart` | Filled only when `role` is `"provider"` or `"consumer"`; the list of counterpart categories the submitter is interested in. `[]` when `role == "intermediary"`. |
| `pairs` | array of `Pair` | Filled only when `role` is `"intermediary"`; candidate provider↔consumer matches. `[]` otherwise. |

A record always has **exactly one** of `counterparts` / `pairs` non-empty
(unless the submitter selected nothing, in which case both may be empty —
the app does not let you download in that state, so a real export always has
one populated).

## Geography and activity codes used throughout

- **Country**: 2-letter Eurostat/NUTS country code, e.g. `"FR"`, `"DE"`. Full code → name list: [`nuts_reference.csv`](nuts_reference.csv) (parsed at runtime into `app/data.py::COUNTRY_NAMES`).
- **NUTS-1 region**: Eurostat NUTS-1 code within a country, e.g. `"FRI"`. An empty region list means "the whole country" / "indifferent to region". Full code → name list: [`nuts_reference.csv`](nuts_reference.csv) (parsed into `app/data.py::NUTS1`). Country and region are collected through a **single combined field** (`widgets.pick_location` / `widgets.pick_locations_multi`): the same dropdown lists whole countries and their NUTS-1 regions together, so picking `"FR"` means "anywhere in France" and picking `"FRI"` means just that region — there is no separate region question.
- **Category**: CEADS' own high-level actor typology, codes `C1`–`C12`. Definitions: [`sector_specific_expert_knowledge.md`](sector_specific_expert_knowledge.md) (parsed into `app/data.py::CATS`).
- **NACE**: EU NACE Rev.2 activity code, e.g. `"01.1"`. Most categories offer 3-digit (group) codes; some offer 4-digit (class) codes for finer detail. Code → label lookup: [`nace_reference.csv`](nace_reference.csv). Which categories get which granularity, and which anchors expand, is expert-knowledge content specified in [`sector_specific_expert_knowledge.md`](sector_specific_expert_knowledge.md) (parsed at runtime by `app/data.py::NACE_OPTIONS`) — not this document. An empty NACE list means "any activity within the category".
- **Quantity**: an integer 0–3 rating of business-value potential for a `Counterpart` or `Pair` (see below). Always present; defaults to `1` when "quantity mode" is off.

## Quantity (business-value potential)

Every `Counterpart` and every `Pair` carries a `quantity` field, an integer
from 0 to 3 rating the potential for a valuable business exchange between the
two sides. It combines *likelihood* of a match and *magnitude* of value
created if it happens — the two tend to move together.

| Value | Meaning |
|---|---|
| `0` | No potential — this pairing essentially never leads to a business exchange. |
| `1` | Limited — a match happens occasionally, and value created is modest when it does. |
| `2` | Meaningful — a match is fairly likely and would create solid business value. |
| `3` | Near-systematic — this pairing almost always represents a genuine business interest, with high potential for value creation. |

Whether this rating uses two values or four is **not an in-app UI control** —
respondents can't see or flip it mid-session. It's set per deployment link via
the `binary_value` URL query parameter (`?binary_value=0` or `?binary_value=1`),
falling back to the hardcoded `config.QUANTITY_MODE` in `app/config.py` when
the URL carries no (valid) `binary_value`. Read and stored into
`st.session_state["quantity_mode"]` once per session by
`config.init_session_from_query_params()`, called at the top of both
`app_select.py` and `app_assess.py`:

- **`binary_value=1`** (or `QUANTITY_MODE = False`, the hardcoded default):
  in `app_select.py`, every `quantity` is fixed at `1` and no extra question
  is shown. In `app_assess.py`, the respondent still gives an explicit binary
  judgment, recorded as `1` ("possible match") or `0` ("no potential") — see
  [Assessment output](#assessment-output-appassesspy).
- **`binary_value=0`** (or `QUANTITY_MODE = True`): the respondent rates each
  counterpart/pair/candidate on the 0–3 scale above, in both apps.

Because `quantity` is always present with a well-defined default, downstream
tooling can consume it uniformly without checking whether quantity mode was
on for a given submission.

## URL query parameters

Both apps read two optional query parameters, captured once per session
(they survive Streamlit's internal page navigation even though it can drop
them from the visible URL — see `config.init_session_from_query_params`):

| Parameter | Values | Effect |
|---|---|---|
| `organization_name` | any string | Embedded in the exported JSON's filename (see below). Defaults to `"unspecified"` when absent. |
| `binary_value` | `"0"` or `"1"` | Sets quantity-rating mode for the session — see [Quantity](#quantity-business-value-potential) above. Falls back to `config.QUANTITY_MODE` when absent or not `"0"`/`"1"`. |

Example: `https://<app-url>/?organization_name=Acme+Coop&binary_value=0`.

**Export filename**: `<app>_<organization_name>_<timestamp>.json`, e.g.
`select_Acme_Coop_20260818-153045.json` — built by
`schema.build_export_filename(app_name)`, where `app_name` is the literal
`"select"` or `"assess"` and `organization_name` is sanitized to filename-safe
characters.

## `self_profile` (depends on `role`)

**When `role` is `"provider"` or `"consumer"`** — one location, but one or
more activities (a farm that is both a crop grower and does agritourism, for
instance):

```json
{
  "country": "FR",
  "nuts1": ["FRI"],
  "activities": [
    {
      "category": "C1",
      "category_name": "Primary producers (farmers)",
      "nace": ["01.1", "01.2"]
    }
  ]
}
```

- `country` (string, required): the actor's country.
- `nuts1` (array of strings, 0 or 1 items): the actor's NUTS-1 region, if a
  specific one was picked instead of the whole country; `[]` = whole country.
  Country and region come from the single combined location field described
  above, so this array never holds more than one code.
- `activities` (array of `Activity`, at least 1 required): every activity
  category the actor operates under. Each item:
  - `category` (string, required): a `C1`–`C12` code.
  - `category_name` (string): human-readable label for `category`.
  - `nace` (array of strings): NACE codes within `category`; `[]` = any activity in that category.

**When `role` is `"intermediary"`** — only the country is collected (the
intermediary itself is not a data provider or consumer, just the party
proposing matches):

```json
{ "country": "BE" }
```

## `Counterpart` (item of the `counterparts` array)

One entry per actor category the submitter (a provider or consumer) is
interested in on the *other* side of the exchange. Geography and NACE are
optional refinements — empty means "no preference".

```json
{
  "category": "C4",
  "category_name": "Food & beverage processing industry",
  "geo": ["DE1", "FR", "IT"],
  "nace": ["10.1", "10.5"],
  "quantity": 2
}
```

- `category` (string, required): `C1`–`C12` code of the counterpart type wanted.
- `category_name` (string): human-readable label for `category` (redundant with `category`, kept for readability).
- `geo` (array of strings): picked from the same single combined country/region field described above — a mix of country codes and/or NUTS-1 codes. A bare country code (e.g. `"FR"`) means "anywhere in France"; a NUTS-1 code (e.g. `"DE1"`) narrows to that region. `[]` = any location.
- `nace` (array of strings): NACE codes of interest within `category`. `[]` = any activity in that category.
- `quantity` (integer, required, 0–3): business-value potential rating (see [Quantity](#quantity-business-value-potential)); `1` if quantity mode was off.

## `Pair` (item of the `pairs` array, intermediary mode only)

One candidate provider↔consumer match proposed by the intermediary. `provider`
and `consumer` are both `Party` objects with an identical shape; `quantity`
sits on the pair itself (it rates the match, not either side individually).

```json
{
  "provider": {
    "country": "FR",
    "nuts1": ["FRI"],
    "category": "C1",
    "category_name": "Primary producers (farmers)",
    "nace": ["01.1"]
  },
  "consumer": {
    "country": "DE",
    "nuts1": ["DE1"],
    "category": "C4",
    "category_name": "Food & beverage processing industry",
    "nace": ["10.1"]
  },
  "quantity": 2
}
```

`Party` fields:

- `country` (string, required)
- `nuts1` (array of strings, 0 or 1 items) — from the same single combined location field; `[]` = whole country
- `category` (string, required) — `C1`–`C12`
- `category_name` (string) — human-readable label for `category`
- `nace` (array of strings) — `[]` = any activity in the category

`Pair`-level field:

- `quantity` (integer, required, 0–3): business-value potential rating for this specific provider↔consumer match (see [Quantity](#quantity-business-value-potential)); `1` if quantity mode was off.

## Full examples

**Provider**, based in France (Nouvelle-Aquitaine), a farmer (C1) who also
runs a small cooperative (C2), interested in two consumer categories:

```json
{
  "role": "provider",
  "self_profile": {
    "country": "FR",
    "nuts1": ["FRI"],
    "activities": [
      {
        "category": "C1",
        "category_name": "Primary producers (farmers)",
        "nace": ["01.1"]
      },
      {
        "category": "C2",
        "category_name": "Cooperatives & producer organisations",
        "nace": []
      }
    ]
  },
  "counterparts": [
    {
      "category": "C4",
      "category_name": "Food & beverage processing industry",
      "geo": [],
      "nace": ["10.1"],
      "quantity": 3
    },
    {
      "category": "C7",
      "category_name": "Agri-tech, digital & data-infrastructure providers",
      "geo": ["FR", "BE"],
      "nace": [],
      "quantity": 1
    }
  ],
  "pairs": []
}
```

*(quantities above assume quantity mode was on; with it off both entries would carry `"quantity": 1`.)*

**Consumer**, based in Germany, interested in French/Italian primary producers:

```json
{
  "role": "consumer",
  "self_profile": {
    "country": "DE",
    "nuts1": ["DE1"],
    "activities": [
      {
        "category": "C4",
        "category_name": "Food & beverage processing industry",
        "nace": ["10.1", "10.5"]
      }
    ]
  },
  "counterparts": [
    {
      "category": "C1",
      "category_name": "Primary producers (farmers)",
      "geo": ["FR", "ITC"],
      "nace": [],
      "quantity": 1
    }
  ],
  "pairs": []
}
```

**Intermediary**, based in Belgium, proposing one match:

```json
{
  "role": "intermediary",
  "self_profile": { "country": "BE" },
  "counterparts": [],
  "pairs": [
    {
      "provider": {
        "country": "FR",
        "nuts1": ["FRI"],
        "category": "C1",
        "category_name": "Primary producers (farmers)",
        "nace": ["01.1"]
      },
      "consumer": {
        "country": "DE",
        "nuts1": ["DE1"],
        "category": "C4",
        "category_name": "Food & beverage processing industry",
        "nace": ["10.1"]
      },
      "quantity": 3
    }
  ]
}
```

## Formal JSON Schema (draft-07)

For programmatic validation (e.g. before ingesting exports into the future
training-data pipeline):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CEADSCounterpartSelection",
  "type": "object",
  "required": ["role", "self_profile", "counterparts", "pairs"],
  "additionalProperties": false,
  "properties": {
    "role": { "type": "string", "enum": ["provider", "consumer", "intermediary"] },
    "self_profile": {
      "oneOf": [
        {
          "type": "object",
          "required": ["country", "nuts1", "activities"],
          "additionalProperties": false,
          "properties": {
            "country": { "type": "string", "pattern": "^[A-Z]{2}$" },
            "nuts1": { "type": "array", "items": { "type": "string" }, "maxItems": 1 },
            "activities": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "object",
                "required": ["category", "category_name", "nace"],
                "additionalProperties": false,
                "properties": {
                  "category": { "type": "string", "pattern": "^C(1[0-2]|[1-9])$" },
                  "category_name": { "type": "string" },
                  "nace": { "type": "array", "items": { "type": "string" } }
                }
              }
            }
          }
        },
        {
          "type": "object",
          "required": ["country"],
          "additionalProperties": false,
          "properties": {
            "country": { "type": "string", "pattern": "^[A-Z]{2}$" }
          }
        }
      ]
    },
    "counterparts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["category", "category_name", "geo", "nace", "quantity"],
        "additionalProperties": false,
        "properties": {
          "category": { "type": "string", "pattern": "^C(1[0-2]|[1-9])$" },
          "category_name": { "type": "string" },
          "geo": { "type": "array", "items": { "type": "string" } },
          "nace": { "type": "array", "items": { "type": "string" } },
          "quantity": { "type": "integer", "minimum": 0, "maximum": 3 }
        }
      }
    },
    "pairs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["provider", "consumer", "quantity"],
        "additionalProperties": false,
        "properties": {
          "provider": { "$ref": "#/definitions/party" },
          "consumer": { "$ref": "#/definitions/party" },
          "quantity": { "type": "integer", "minimum": 0, "maximum": 3 }
        }
      }
    }
  },
  "definitions": {
    "party": {
      "type": "object",
      "required": ["country", "nuts1", "category", "category_name", "nace"],
      "additionalProperties": false,
      "properties": {
        "country": { "type": "string", "pattern": "^[A-Z]{2}$" },
        "nuts1": { "type": "array", "items": { "type": "string" }, "maxItems": 1 },
        "category": { "type": "string", "pattern": "^C(1[0-2]|[1-9])$" },
        "category_name": { "type": "string" },
        "nace": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```

## Assessment output (`app_assess.py`)

Instead of letting the respondent pick counterparts, `app_assess.py`
proposes candidates and asks the respondent to rate each one. Its top-level
shape (`schema.build_assessment_payload`):

```json
{
  "role": "provider | consumer | intermediary",
  "self_profile": { ... },
  "assessments": [
    {
      "candidate": { "category": "C10", "category_name": "...", "geo": ["NL3"], "nace": [] },
      "quantity": 1
    }
  ]
}
```

- `self_profile` — identical shape to the one described above (shared `steps/profile.py`).
- `assessments` (array): one entry per rated candidate.
  - `candidate`: for `role` `"provider"`/`"consumer"`, a `Counterpart`-shaped
    object (`category`, `category_name`, `geo`, `nace`). For `role`
    `"intermediary"`, a `{"provider": <candidate>, "consumer": <candidate>}`
    pair, each side shaped the same way.
  - `quantity`: the respondent's rating. When `config.QUANTITY_MODE` is
    `True`, an integer 0–3 (see [Quantity](#quantity-business-value-potential)
    above). When `False`, a plain binary judgment recorded as `1` ("possible
    match") or `0` ("no potential") — not a default, an explicit answer.

**Refinement**: a proposed candidate always starts at category+geography
granularity (`nace: []`), but before rating, the respondent can ask a more
specific version of the same candidate. The respondent only picks the
*dimension* to narrow — "More specific: geography" or "More specific:
industry" — the actual value (which region, which NACE code) is chosen at
random by the app, not the respondent (`steps/assess.py::_refine_geo` /
`_refine_nace`). Geography narrows "any location" → a country → a NUTS-1
region; industry narrows "any activity in this category" → one NACE code,
following the same per-category granularity rules as
`data.py`/`sector_specific_expert_knowledge.md` (e.g. 4-digit for C1). Once a
dimension is narrowed there's no further refinement for it, so a recorded
`candidate` can have `geo`/`nace` at any granularity from "any" up to fully
specific, exactly like a `Counterpart` from `app_select.py`.

Candidates are generated by `steps/assess.py::_random_candidate` (random
category from `taxonomy.CATS`, random location from `widgets.GEO_OPTIONS`,
~20% "any location"); for intermediaries, two independent candidates form
the pair. There is no `counterparts`/`pairs` key in this app's output.

## Where each piece comes from in the code

- `role` ← `st.session_state["role"]`, set in `steps/home.py` (shared by both apps).
- `self_profile` ← built in `steps/profile.py` (shared), using `widgets.pick_location` (provider/consumer) or `widgets.pick_country` (intermediary) for geography, and `widgets.pick_multi_category_activities` for the `activities` array.
- `counterparts` ← built in `steps/select_match.py` (app_select.py only) via `widgets.pick_counterparts`, geography via `widgets.pick_locations_multi`.
- `pairs` ← built in `steps/select_match.py`, either one at a time (`widgets.pick_location` per side + `schema.party_dict` + `schema.pair_dict`) or bulk-imported from CSV (`schema.parse_pairs_csv`), intermediary branch.
- `assessments` ← built in `steps/assess.py` (app_assess.py only), via `schema.build_assessment_payload`.
- `quantity` ← `widgets.pick_quantity` in `app_select.py`, or the rating buttons in `steps/assess.py`; both gated by the hardcoded `config.QUANTITY_MODE` flag (not a UI control — edit `app/config.py` and restart the app). Defaults to `widgets.DEFAULT_QUANTITY` (`1`) in `app_select.py` when off; `app_assess.py` always records an explicit `0`/`1` even when off.
- Final assembly and download: `schema.build_payload` / `schema.build_assessment_payload` / `schema.download_json_button`.
