# Matchmaker

Two small Streamlit apps for mapping the potential for agricultural
data-sharing across Europe: respondents describe themselves (data provider,
data consumer, or intermediary), then either pick their own list of desired
counterparts or rate system-proposed candidate matches.

- **`app_select.py`** — respondent builds their own list of counterparts
  (or provider/consumer pairs, for intermediaries), optionally rating
  business-value potential.
- **`app_assess.py`** — the app proposes candidate matches one at a time;
  the respondent rates each, and can ask to see a more specific version of
  a candidate (the respondent picks the dimension to narrow — geography or
  industry — the app currently picks the actual value at random).

The two apps share their first two steps (role selection, self profile) via
`app/steps/`, so there's no duplicated code between them.

Documentation is split by audience:

- [`sector_specific_expert_knowledge.md`](sector_specific_expert_knowledge.md)
  — the **expert-knowledge spec**: which home-cooked actor categories exist
  above NACE, which NACE codes anchor each one, and the desired
  industry/geography granularity. Parsed at runtime — this file is the
  source of truth, not the Python code.
- [`nace_reference.csv`](nace_reference.csv) / [`nuts_reference.csv`](nuts_reference.csv)
  — plain code → label lookups (NACE activity codes; countries and their
  NUTS-1 regions), each with a pointer to the Eurostat classification it's
  derived from. Both parsed at runtime by `app/data.py`.
- [`json_export_format.md`](json_export_format.md) — the **technical spec**:
  the input/output JSON shape for both apps, for programmers and AI models.
  It deliberately says nothing about what the category/NACE/geography
  values mean.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app/app_select.py   # http://localhost:8501
streamlit run app/app_assess.py   # http://localhost:8502
```

## Deploying (e.g. Streamlit Community Cloud)

The two apps are independent entry points into the same codebase, so they
need to be deployed separately, both pointing at this repo:

- App 1 — main file path: `app/app_select.py`
- App 2 — main file path: `app/app_assess.py`

Both resolve the root `requirements.txt` automatically — Community Cloud
checks the repo root as well as next to the entry-point script.

## Data & privacy

Nothing is written to server-side storage: all responses live in the
browser session's memory for the duration of that session and are only
persisted if the respondent explicitly clicks "Download ... (JSON)".

## License

MIT — see [LICENSE](LICENSE).
