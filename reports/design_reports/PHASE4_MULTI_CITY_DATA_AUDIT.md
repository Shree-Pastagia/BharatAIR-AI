# BharatAir Phase 4 — India-Wide CPCB PM2.5 Data Audit

**Audit date:** 2026-11-17  
**Dataset audited:** XKDR India Air Quality Database, `source=cpcb_caaqm`, `parameter=PM2.5`  
**Decision:** **CONDITIONAL GO** for a bounded multi-city historical study through 2025-09-01. **No GO for a CPCB 2026 extension:** no CPCB PM2.5 observations were returned in 2026, and the latest CPCB record is 2025-09-01 23:00 IST.

## Executive summary

The authenticated XKDR API supports reproducible, source- and pollutant-filtered retrieval. We retrieved 17,594,014 raw hourly CPCB CAAQM PM2.5 records across 549 site IDs, from 2009-01-01 through 2025-09-01. The 18 year-bounded API queries (2009–2026 Q1) were untruncated and totaled 60,698,411 bytes. The 2026 query returned zero CPCB rows. The CPCB dataset therefore provides substantial multi-city historical depth, but it does **not** provide current 2026 CPCB data.

Under the predeclared screening tiers, 310 stations are Tier A, 165 Tier B and 78 Tier C. Seven of the eight lead stations selected for Delhi, Hyderabad, Bengaluru, Mumbai, Ahmedabad, Chennai, Kolkata and Pune are Tier A; Pune's longest-history choice is Tier B. The strongest cities have years of hourly coverage and good recent coverage through 2025-09-01, but the eight selected station series do not form a dense shared hourly panel: all eight have ≥80% coverage in only 25 common full calendar months over a 70-month common span.

The original Phase 3 anchor, `site_1422` Dwarka-Sector 8, DPCC, is supported by 63,178 PM2.5 rows from 2018-02-01 10:00 through 2025-09-01 23:00 IST. It has 4.95% missingness within its active span, 88 months with ≥80% coverage, and no duplicate, off-hour, null, nonnumeric or negative measurements. This audit did not modify the canonical Phase 3 dataset, configuration, runs, models or test gate.

The 2026 tail belongs to another network. A separate Embassy-only 2026-Q1 check returned 4,047 readings from **US Embassy–New Delhi** (`DS1010001`) and **US Embassy–Hyderabad** (`DS1010005`), all at `:30`, through 2026-03-27 23:30 IST. Those records were isolated and excluded from CPCB counts, rankings and recommendations.

## Source, identity and retrieval

XKDR's export metadata reports 196.5 million readings in 207 monthly files across 558 stations and 15 pollutants, published through 2026-03 in the file index. The full all-network/all-pollutant index is 409.6 MB; this audit downloaded only CPCB CAAQM PM2.5, 60.7 MB. Authentication used the existing project key loader. The key was never printed or logged.

The CPCB measurement extract contains 549 distinct station IDs with PM2.5 and the 553-row current XKDR CPCB station metadata provides names, locations and pollutant lists. Four current metadata IDs (`site_165`, `site_166`, `site_274`, `site_5367`) list no PM2.5 observation in the retrieved period. Metadata has both city and state populated for 245 distinct pairs; 62 observed stations lack a state label and 29 lack both city and state. The [city summary](PHASE4_CITY_COVERAGE_SUMMARY.csv) retains unknown-location groups instead of assigning guessed geography. The All-India CPCB CCR register PDF snapshot contains 358 site codes; exact code matching finds 348 of 549 PM2.5-observed IDs. The remaining 201 are retained in the inventory and flagged as absent from this register snapshot; no station was discarded because metadata was absent. The official register identifies `site_1422` as Dwarka-Sector 8, Delhi, operated by DPCC.

The returned PM2.5 Parquet schema uses `station_id`, `parameter_name`, `unit`, `collected_at`, and `value`. All records are CPCB source-filtered; unit is `µg/m³`. XKDR documents naive IST timestamps; every timestamp in the extract is on the hour. CPCB's transmission protocol describes 15-minute station transmissions, but quarter-hour rows are not present in this delivered extract. The observed cadence is hourly and should be represented as such.

XKDR documents CC BY 4.0 with attribution to the India Air Quality Database/XKDR Forum and source networks. It states measurements are as received, preliminary and not warranted for regulatory or health decisions. See [XKDR API/data notes](https://airquality.xkdr.org/), [CPCB station register](https://app.cpcbccr.com/ccr_docs/caaqms_list_All_India.pdf), and [CPCB CAAQM transmission protocol](https://app.cpcbccr.com/ccr_docs/Protocol_CAAQM.pdf).

## Coverage and station eligibility

The full station audit is in [PHASE4_STATION_INVENTORY.csv](PHASE4_STATION_INVENTORY.csv); ranked screening tiers are in [PHASE4_STATION_ELIGIBILITY.csv](PHASE4_STATION_ELIGIBILITY.csv), and city counts are in [PHASE4_CITY_COVERAGE_SUMMARY.csv](PHASE4_CITY_COVERAGE_SUMMARY.csv). Those files contain exact station observation counts, date ranges, expected/observed hourly slots, active-span missingness, reporting days/months/years, monthly coverage counts, gaps, duplicates, invalids, units, operators and rank inputs.

Coverage denominator: from the first through last observed on-hour timestamp for that station, inclusive. Expected slots are hourly. Month-level expected slots are clipped to station start/end hours; the first/last station-month is explicitly marked partial. Longest missing interval is the largest internal gap between distinct on-hour observations; leading/trailing unavailable periods outside the active span are not included. No interpolation, forward filling, outlier deletion or station averaging was performed.

| Screening tier | Stations | Rule |
|---|---:|---|
| A | 310 | ≥2 represented years; ≥70% active-span coverage; ≥75% of active months at ≥80% hourly coverage; ≥60% of active Jan 2024–Sep 2025 months at ≥80%; no duplicate, off-hour, null/nonnumeric or negative rows |
| B | 165 | ≥1 represented year; ≥50% active-span coverage; ≥50% of active months at ≥80% |
| C | 78 | 74 observed stations do not meet B; 4 currently listed stations have no PM2.5 rows in this extract |

These are transparent project-screening bands, not regulatory quality grades. Sensitivity counts vary with thresholds: among stations with ≥2 represented years, 464 meet ≥50% active coverage and ≥50% of active months at ≥80%; 321 meet ≥70% and ≥75%; 119 meet ≥90% active-span coverage and ≥50% months at ≥80%. The main Tier A additionally requires recent-month coverage and clean timestamps/values.

### Data quality

- Summed station active spans: 21,586,809 expected hourly slots, 17,594,014 observed distinct on-hour slots, or 81.50% weighted coverage. This sums overlapping stations; it is **not** national ambient coverage.
- Median station active-span coverage: 83.64%; 10th percentile: 64.95%.
- Duplicate timestamp rows: 0. Off-hour timestamps: 0. Null timestamps: 0. Null/nonnumeric values: 0. Negative concentrations: 0.
- Values ≥500 µg/m³: 43,832 records; ≥1,000 µg/m³: 488. Values are retained as received and flagged. They are not automatically considered erroneous.
- All extracted values use `µg/m³`; there are no mixed units in this CPCB PM2.5 extract.

### Selected city stations

These are data-screening recommendations, not city-level averages. The city-specific station and operator remain separate.

| City | Recommended station | Operator | First to latest PM2.5 (IST) | Rows | Active-span missingness | Tier |
|---|---|---|---|---:|---:|:---:|
| Delhi | `site_113` Shadipur (use `site_1422` as Phase 3 continuity anchor) | CPCB; DPCC for site_1422 | 2015-03-23 to 2025-09-01; site_1422: 2018-02-01 10:00 to 2025-09-01 23:00 | 81,965; site_1422: 63,178 | 10.49%; site_1422: 4.95% | A |
| Hyderabad | `site_294` Sanathnagar | TSPCB | 2015-03-31 to 2025-09-01 23:00 | 80,379 | 12.05% | A |
| Bengaluru | `site_1555` Hombegowda Nagar | KSPCB | 2018-07-03 to 2025-09-01 23:00 | 56,794 | 9.59% | A |
| Mumbai | `site_5107` Chhatrapati Shivaji Intl. Airport T2 | MPCB | 2019-06-04 to 2025-09-01 23:00 | 48,570 | 11.30% | A |
| Ahmedabad | `site_308` Maninagar | GPCB | 2015-01-28 to 2025-09-01 23:00 | 74,782 | 19.47% | A |
| Chennai | `site_288` Velachery Residential Area | CPCB | 2015-04-06 to 2025-09-01 23:00 | 81,255 | 10.94% | A |
| Kolkata | `site_309` Victoria | WBPCB | 2018-04-10 to 2025-09-01 23:00 | 58,938 | 9.10% | A |
| Pune | `site_292` Karve Road | MPCB | 2015-06-17 to 2025-05-23 21:00 | 63,900 | 26.61% | B |

For Pune, choose `site_292` when long history is the priority; consider `site_5404` Mhada Colony (IITM) for recency (29,478 rows through 2025-09-01 23:00, 29.95% missingness, Tier B). `site_5409` Revenue Colony-Shivajinagar has 30,713 rows through 2025-08-10, 26.07% missingness and the strongest recent-month ratio among these options. Predeclare one primary Pune station and use others only as sensitivity stations.

## Common-period findings

The eight city lead stations share 70 full calendar months from 2019-07 through 2025-04, but all eight have ≥80% coverage in only 25 of those months; those months are discontinuous. All eight meet ≥70% coverage in 33 common full months. At least one Tier A station in 100 or more cities has ≥80% coverage in 32 full months spanning 2021-12 through 2024-12. These findings support station-aware city-specific validation or a ragged pooled panel, not an assumption of a dense, synchronous national panel.

## Research feasibility and recommendation

**Recommended first expansion: Design A, one station per city with separate city forecasts.** Keep `site_1422` as the direct Delhi bridge to Phase 3 and report `site_113` separately as a longer-history Delhi alternative. Use the strongest station selected before training in each other city; treat Pune as a Tier B sensitivity case or defer it from the primary cohort. Design D (leave-one-station-out) is the next transfer study. A pooled panel or leave-one-city-out study is feasible as a later design if all stations remain separate series, splits are chronological, station/time leakage is controlled, and eligible rows are reported per city.

Use PM2.5 concentration in µg/m³ as target, and retain the approved horizons/windows. Do not fill gaps. Require every sample's complete input and forecast timestamps to be present at the same station. Split chronologically per station, preserve the approved boundary purge, fit scaling on training only, and evaluate models against persistence and seasonal-naive baselines on identical per-station timestamps. Keep the final Phase 3 test gate closed; this source audit did not load Phase 3 test values, construct test windows, train models or evaluate test outcomes.

## Limitations

1. CPCB PM2.5 observation availability ends 2025-09-01 in this export despite the overall XKDR file index continuing through 2026-03. A 2026 CPCB extension is unsupported by these records.
2. The official PDF station register snapshot lists 358 codes versus 553 current XKDR CPCB metadata rows. Two hundred one PM2.5-observed IDs do not match that PDF; these retain XKDR metadata but their operator identity needs source-side verification before station-specific conclusions.
3. `CPCB CAAQM` is a multi-operator feed. Data include stations operated by state boards, DPCC, IITM, IMD and others; operator differences may affect comparability. Preserve operator identity.
4. The CPCB protocol describes 15-minute transmission, whereas this extract contains hourly on-the-hour rows. This audit cannot reconstruct the missing quarter-hour readings or establish precisely how each top-of-hour reading summarizes analyzer data.
5. Measurements are reported as received and may be preliminary; no calibration or regulatory QA was performed. High values are retained and flagged.
6. Station coverage is not equal to city/population coverage. Counts and tiers describe the retrieved database only and do not establish India-wide representativeness. The 245 complete state/city pairs exclude 62 stations with missing state metadata and 29 with both city and state missing; those records remain visible in the inventory and city summary.

## Audit artifact map

- [Station inventory](PHASE4_STATION_INVENTORY.csv)
- [City coverage summary](PHASE4_CITY_COVERAGE_SUMMARY.csv)
- [Station eligibility and ranking](PHASE4_STATION_ELIGIBILITY.csv)
- [Common-period analysis](PHASE4_COMMON_PERIOD_ANALYSIS.md)
- [Research design](PHASE4_RESEARCH_DESIGN.md)
- [Source access log](PHASE4_SOURCE_ACCESS_LOG.md)
- Machine-readable summary: `data/phase4_audit/historical_coverage_summary.json`
- Raw CPCB PM2.5 extracts and checksums: `data/phase4_audit/raw_cpcb_pm25/yearly/`
