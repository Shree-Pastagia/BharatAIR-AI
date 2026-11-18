# Phase 4 Common-Period Analysis

## Method

All calculations use only the filtered `source=cpcb_caaqm&parameter=PM2.5` hourly extracts. `collected_at` is naive IST per XKDR. An hourly slot counts only when its timestamp is exactly `HH:00`; no resampling, interpolation or imputation was performed. For each station, the active span runs from its first to last observed hour. Monthly coverage is measured against expected hourly slots inside that active span. The first and last station-months may therefore be partial; the audit labels them. Cross-city full-month comparisons below exclude every station-month whose active span does not cover the full calendar month.

## Aggregate station support

- 549 observed PM2.5 stations; 245 distinct pairs have both city and state metadata populated. There are 263 distinct nonblank city labels. Sixty-two stations lack state metadata and 29 lack both city and state; the summary CSV retains these rows in unknown-location groups.
- Summed station active-span expectation: 21,586,809 hourly slots; observed unique on-hour slots: 17,594,014; weighted active-span coverage: **81.50%**. This sum double-counts calendar hours across station series; it is not a national population coverage rate.
- Median per-station active-span coverage: **83.64%**; 10th percentile: **64.95%**.
- Among Tier A stations, at least one station in at least 50 cities had ≥80% coverage in a full calendar month in 77 months (2019-01 through 2025-08, with gaps). At least 100 cities met that condition in 32 months, spanning 2021-12 through 2024-12. At least 150 cities met it in 16 months, spanning 2023-08 through 2024-11. These are monthly station availability counts, not continuous complete national panels.

## Strongest station per selected city

The table chooses the longest-history candidate among top-ranked stations that also has strong observed coverage; city rank details are in `PHASE4_STATION_ELIGIBILITY.csv`. “Recent good months” counts months with ≥80% station-hour coverage during the station's active portion of Jan 2024–Sep 2025; months after the last available CPCB observation are not silently treated as recent records.

| City | Station | Operating agency | First to last PM2.5 (IST) | Rows | Years represented | Active-span missingness | Recent good months | Tier |
|---|---|---|---|---:|---:|---:|---:|:---:|
| Delhi | `site_113`, Shadipur | CPCB | 2015-03-23 17:00 to 2025-09-01 23:00 | 81,965 | 11 | 10.49% | 18 | A |
| Hyderabad | `site_294`, Sanathnagar | TSPCB | 2015-03-31 00:00 to 2025-09-01 23:00 | 80,379 | 11 | 12.05% | 18 | A |
| Bengaluru | `site_1555`, Hombegowda Nagar | KSPCB | 2018-07-03 17:00 to 2025-09-01 23:00 | 56,794 | 8 | 9.59% | 18 | A |
| Mumbai | `site_5107`, Chhatrapati Shivaji Intl. Airport T2 | MPCB | 2019-06-04 09:00 to 2025-09-01 23:00 | 48,570 | 7 | 11.30% | 18 | A |
| Ahmedabad | `site_308`, Maninagar | GPCB | 2015-01-28 17:00 to 2025-09-01 23:00 | 74,782 | 11 | 19.47% | 18 | A |
| Chennai | `site_288`, Velachery Residential Area | CPCB | 2015-04-06 10:00 to 2025-09-01 23:00 | 81,255 | 11 | 10.94% | 18 | A |
| Kolkata | `site_309`, Victoria | WBPCB | 2018-04-10 09:00 to 2025-09-01 23:00 | 58,938 | 8 | 9.10% | 17 | A |
| Pune | `site_292`, Karve Road | MPCB | 2015-06-17 22:00 to 2025-05-23 21:00 | 63,900 | 11 | 26.61% | 12 | B |

Pune presents a recency/history trade-off. `site_5409` (Revenue Colony-Shivajinagar, IITM) has 30,713 rows from 2020-11-13 14:00 through 2025-08-10 15:00, 26.07% active-span missingness and 17 of 20 active recent months at ≥80%; `site_5404` (Mhada Colony, IITM) has 29,478 rows through 2025-09-01 23:00, 29.95% missingness and 16 of 21 months. Both are Tier B. `site_292` supplies more history, while `site_5404` reaches the network's last date.

## Eight-city full-calendar overlap

Using the eight stations in the table above, the common full-calendar observation-span window is **2019-07 through 2025-04** (70 full calendar months). However, all eight stations individually achieved ≥80% hourly coverage in only **25 of those 70 months**, and those months are discontinuous. All eight achieved ≥70% in 33 full months. Only nine full months in 2024 met the ≥80% criterion for all eight stations; April 2025 is the only shared ≥80% full month in 2025. May 2025 is partial for the long-history Pune `site_292` candidate.

This supports city-specific chronological evaluation and a pooled station panel with uneven observations, but it does not support assuming a dense, complete eight-city hourly panel. A pooled study must retain each site as a separate series and evaluate only samples whose complete input/target timestamps exist. Report availability and errors by city and station; do not fill across gaps or average stations into a city value.

## Delhi pilot overlap

`site_1422` Dwarka-Sector 8, Delhi (DPCC) has 63,178 PM2.5 rows from 2018-02-01 10:00 through 2025-09-01 23:00, 95.05% active-span hourly coverage and 88 months at ≥80% coverage. It is a sound continuity anchor for comparison with Phase 3. The longer-history Delhi candidate `site_113` Shadipur has 81,965 rows from 2015-03-23 17:00 through 2025-09-01 23:00 and 10.49% active-span missingness. Keep these as distinct station series; do not concatenate or average them.

## Network cutoff and non-CPCB records

The latest CPCB CAAQM PM2.5 record is 2025-09-01 23:00 IST. The September 2025 coverage is therefore a *partial month* across the overall source; it must not be interpreted as full-month CPCB availability. XKDR's small 2025-10–2026-03 index files are not CPCB PM2.5. A separate Embassy-only 2026-Q1 probe found 4,047 readings from two Embassy station IDs at `:30`, latest 2026-03-27 23:30 IST. Those records are excluded from all CPCB overlaps and must never be used to extend a CPCB station series.
