This file is what makes the two apps (`app_select.py` and `app_assess.py`) specific to agriculture. 
It is meant to incorporate expert knowledge about this sector. 

The main contribution of this file is to define ad hoc categories of economic actors and 
its correspondence with the NACE classification of activities. 
More precisely, it contains **two main kinds of expert input**:

1. **Industry coverage & granularity** — which NACE activities are relevant
   to this app at all, and how finely to refine each one (a whole division?
   a group? individual classes?). Specified per category below.
2. **Industry-specific grouping of NACE into sector-specific names** —
   bundling one or more NACE codes into a single, intuitively-named category
   (e.g. "Primary producers (farmers)") that means something to people in
   the sector. This is the category list itself, below.

`app/data.py` **parses this file** at import time — it is the single source
of truth for the app's category list, NACE anchors, and granularity. There
is no separate hard-coded copy to keep in sync: edit this file and the app
picks it up on next run.

NACE code → label lookups are **not** duplicated here — they live in
[`nace_reference.csv`](nace_reference.csv) (see [Data sources](#data-sources)
below), which holds the **full** NACE Rev. 2 classification (975 codes:
every division, group and class). The labels shown next to each code below
are copied from there **purely for human readability** — they are not
parsed; only the backtick-wrapped codes are. Edit a label here and nothing
changes; edit `nace_reference.csv` and it does. Every code used as an anchor
below must exist in `nace_reference.csv` — the app validates this at
startup and fails loudly (naming the bad code) if one doesn't, since that
file is the authority on what counts as a real NACE code.

Note that this file is deliberately separate from [`json_export_format.md`](json_export_format.md),
which only documents the technical shape of the app's output for programmers/AI models.

### How to read (and edit) the category list

Each category is its own subsection below (`### C<n> — Name`), with:

- a one-line *Scope* (prose, not parsed — just orients a human reader),
- a **NACE granularity** line, `3-digit` or `4-digit`, which controls how
  finely the app lets a respondent refine within that category,
- a bulleted list of NACE codes, **one per line**. A parent group is
  sometimes shown with its children indented beneath it, purely to mirror
  the real NACE hierarchy for readability — only the backtick-wrapped codes
  are parsed, and listing both a parent and its children is safe (a code
  offered twice is silently de-duplicated), so nesting is a readability aid,
  not a parsing requirement.
- **`4-digit` categories only list the classes actually worth offering**,
  not necessarily every child a group has. When some of a group's children
  are deliberately left out (e.g. crops essentially absent from European
  agriculture), that group is written as a **plain-text heading, not
  backtick-coded** — this stops the excluded children from being silently
  pulled back in by auto-expansion. C1 below has several examples.
- Anchors are listed at whichever level (division/group/class) is the most
  **intuitive** whole unit for that category — e.g. C5 anchors on bare
  2-digit divisions (`46` = the entire "Wholesale trade" division) rather
  than an arbitrary group within it, since the category means the whole
  division. There's no official NACE code for "a whole division as a
  group" (no `46.0`-style code) — a division code (no dot) is simply used
  directly as an anchor when that's what's meant.

**C1** (Primary producers) and **C4** (Food & beverage processing) are set
to `4-digit` — these are the two activity fields this data collection cares
about most, so they get class-level detail (e.g. "dairy cattle" rather than
just "animal production"). **C10**, despite also touching
agriculture-adjacent codes, stays at `3-digit` — it describes
support/standards bodies, not the primary-production or processing activity
itself, so finer NACE detail there isn't informative. Every other category
defaults to `3-digit`. This
is a deliberate per-category choice, not a limitation of
`nace_reference.csv` — that file has 4-digit children for essentially every
division, so any category could be switched to `4-digit` by changing its
granularity line below.

## Categories

### C1 — Primary producers (farmers)

*Scope:* Crop growers, livestock/dairy farmers, mixed farms, contractors.
**NACE granularity:** 4-digit

- Growing of non-perennial crops (excludes sugar cane — not grown in mainland Europe)
  - `01.11` — Growing of cereals (except rice), leguminous crops and oil seeds
  - `01.12` — Growing of rice
  - `01.13` — Growing of vegetables and melons, roots and tubers
  - `01.15` — Growing of tobacco
  - `01.16` — Growing of fibre crops
  - `01.19` — Growing of other non-perennial crops
- Growing of perennial crops (excludes tropical/subtropical fruits and beverage crops — coffee, tea, cocoa — not grown in mainland Europe)
  - `01.21` — Growing of grapes
  - `01.23` — Growing of citrus fruits
  - `01.24` — Growing of pome fruits and stone fruits
  - `01.25` — Growing of other tree and bush fruits and nuts
  - `01.26` — Growing of oleaginous fruits
  - `01.28` — Growing of spices, aromatic, drug and pharmaceutical crops
  - `01.29` — Growing of other perennial crops
- `01.3` — Plant propagation
- Animal production (excludes camels and camelids — not farmed in Europe)
  - `01.41` — Raising of dairy cattle
  - `01.42` — Raising of other cattle and buffaloes
  - `01.43` — Raising of horses and other equines
  - `01.45` — Raising of sheep and goats
  - `01.46` — Raising of swine/pigs
  - `01.47` — Raising of poultry
  - `01.49` — Raising of other animals
- `01.5` — Mixed farming
- `01.6` — Support activities to agriculture and post-harvest crop activities
  - `01.61` — Support activities for crop production
  - `01.62` — Support activities for animal production
  - `01.63` — Post-harvest crop activities
  - `01.64` — Seed processing for propagation

### C2 — Cooperatives & producer organisations

*Scope:* Farmer cooperatives, POs aggregating primary producers.
**NACE granularity:** 3-digit

- `01.6` — Support activities to agriculture and post-harvest crop activities
- `46.2` — Wholesale of agricultural raw materials and live animals
- `94.1` — Activities of business, employers and professional membership organisations

### C3 — Farm advisory & extension services (AKIS)

*Scope:* Advisors, extension, farm-advisory service providers, veterinarians.
**NACE granularity:** 3-digit

- `74.9` — Other professional, scientific and technical activities n.e.c.
- `01.6` — Support activities to agriculture and post-harvest crop activities
- `75` — Veterinary activities

### C4 — Food & beverage processing industry

*Scope:* Dairies, meat/veg processors, wineries, food manufacturers.
**NACE granularity:** 4-digit

- `10.1` — Processing and preserving of meat and production of meat products
  - `10.11` — Processing and preserving of meat
  - `10.12` — Processing and preserving of poultry meat
  - `10.13` — Production of meat and poultry meat products
- `10.2` — Processing and preserving of fish, crustaceans and molluscs
- `10.3` — Processing and preserving of fruit and vegetables
  - `10.31` — Processing and preserving of potatoes
  - `10.32` — Manufacture of fruit and vegetable juice
  - `10.39` — Other processing and preserving of fruit and vegetables
- `10.4` — Manufacture of vegetable and animal oils and fats
  - `10.41` — Manufacture of oils and fats
  - `10.42` — Manufacture of margarine and similar edible fats
- `10.5` — Manufacture of dairy products
  - `10.51` — Operation of dairies and cheese making
  - `10.52` — Manufacture of ice cream
- `10.6` — Manufacture of grain mill products, starches and starch products
  - `10.61` — Manufacture of grain mill products
  - `10.62` — Manufacture of starches and starch products
- `10.7` — Manufacture of bakery and farinaceous products
  - `10.71` — Manufacture of bread; manufacture of fresh pastry goods and cakes
  - `10.72` — Manufacture of rusks and biscuits; manufacture of preserved pastry goods and cakes
  - `10.73` — Manufacture of macaroni, noodles, couscous and similar farinaceous products
- `10.8` — Manufacture of other food products
  - `10.81` — Manufacture of sugar
  - `10.82` — Manufacture of cocoa, chocolate and sugar confectionery
  - `10.83` — Processing of tea and coffee
  - `10.84` — Manufacture of condiments and seasonings
  - `10.85` — Manufacture of prepared meals and dishes
  - `10.86` — Manufacture of homogenised food preparations and dietetic food
  - `10.89` — Manufacture of other food products n.e.c.
- `10.9` — Manufacture of prepared animal feeds
  - `10.91` — Manufacture of prepared feeds for farm animals
  - `10.92` — Manufacture of prepared pet foods
- `11.0` — Manufacture of beverages
  - `11.01` — Distilling, rectifying and blending of spirits
  - `11.02` — Manufacture of wine from grape
  - `11.03` — Manufacture of cider and other fruit wines
  - `11.04` — Manufacture of other non-distilled fermented beverages
  - `11.05` — Manufacture of beer
  - `11.06` — Manufacture of malt
  - `11.07` — Manufacture of soft drinks; production of mineral waters and other bottled waters

### C5 — Downstream trade, logistics & retail

*Scope:* Wholesalers, retailers, logistics, premium markets.
**NACE granularity:** 3-digit

- `46` — Wholesale trade, except of motor vehicles and motorcycles
- `47` — Retail trade, except of motor vehicles and motorcycles
- `49` — Land transport and transport via pipelines
- `52` — Warehousing and support activities for transportation

### C6 — Upstream input & machinery suppliers

*Scope:* Agri-machinery manufacturers & dealers; seed/fertiliser/agrochemical/feed suppliers.
**NACE granularity:** 3-digit

- `28.3` — Manufacture of agricultural and forestry machinery
- `46.61` — Wholesale of agricultural machinery, equipment and supplies
- `20.1` — Manufacture of basic chemicals, fertilisers and nitrogen compounds, plastics and synthetic rubber in primary forms
- `20.2` — Manufacture of pesticides and other agrochemical products
- `10.9` — Manufacture of prepared animal feeds

### C7 — Agri-tech, digital & data-infrastructure providers

*Scope:* FMIS, IoT, EO/GIS, AI software; data-space connectors, national DSIs & digital platforms.
**NACE granularity:** 3-digit

- `62.0` — Computer programming, consultancy and related activities
- `63.1` — Data processing, hosting and related activities; web portals
- `58.2` — Software publishing
- `61` — Telecommunications

### C8 — Research, academia & innovation actors

*Scope:* Universities, RTOs, testbeds (agrifoodTEF), EOSC, testing laboratories.
**NACE granularity:** 3-digit

- `72.1` — Research and experimental development on natural sciences and engineering
- `72.2` — Research and experimental development on social sciences and humanities
- `85.4` — Higher education
- `71.2` — Technical testing and analysis

### C9 — Public authorities & policy actors

*Scope:* Paying agencies, ministries, DG AGRI, statistical & inspection bodies.
**NACE granularity:** 3-digit

- `84.1` — Administration of the State and the economic and social policy of the community

### C10 — Standards, certification & sector data bodies

*Scope:* Breeding/genetic-recording associations (ICAR), certification & traceability bodies.
**NACE granularity:** 3-digit

- `01.6` — Support activities to agriculture and post-harvest crop activities
- `71.2` — Technical testing and analysis
- `94.1` — Activities of business, employers and professional membership organisations

### C12 — Insurance & risk-management actors

*Scope:* Agri-insurers, risk-management / risk-pooling actors.
**NACE granularity:** 3-digit

- `65` — Insurance, reinsurance and pension funding, except compulsory social security
- `66.2` — Activities auxiliary to insurance and pension funding

## Geography granularity

The app offers **one uniform level of regional refinement across every
country: NUTS-1**. There is no per-country configuration — every country
in [`nuts_reference.csv`](nuts_reference.csv) is offered both as a whole
country and broken down into its NUTS-1 regions, through a single combined
field (see `widgets.pick_location`). This is a deliberate simplicity choice,
not a limitation of the data: NUTS-2/3 breakdowns exist at the source but
are not exposed, since finer regional detail was judged not to be worth the
added complexity for respondents.

## Data sources

- **NACE codes & labels**: [`nace_reference.csv`](nace_reference.csv) — the
  full NACE Rev. 2 (Statistical Classification of Economic Activities in the
  European Community) code list: all 88 divisions, 272 groups and 615
  classes. Transcribed from Eurostat's official structure document, [*NACE
  Rev. 2 — Statistical classification of economic activities in the
  European Community*](https://ec.europa.eu/eurostat/documents/3859598/5902521/KS-RA-07-015-EN.PDF.pdf/dd5443f5-b886-40e4-920d-9df03590ff91)
  (KS-RA-07-015-EN), Part III "Detailed Structure of NACE Rev. 2" — not a
  machine-readable export from Eurostat, so treat it as authoritative for
  this app but report any transcription error found against the source PDF.
- **Countries & NUTS-1 regions**: [`nuts_reference.csv`](nuts_reference.csv)
  — country codes/names and their NUTS-1 regions. Original classification:
  [Eurostat, NUTS — correspondence
  tables](https://ec.europa.eu/eurostat/web/nuts/correspondence-tables). The
  CSV is a reformatted extract, not a verbatim export.

## Notes

- Categories are **not mutually exclusive** — a respondent can select
  several at once (see `widgets.pick_multi_category_activities` /
  `pick_counterparts`), since a real actor often spans more than one (e.g. a
  farm that also runs a small cooperative).
