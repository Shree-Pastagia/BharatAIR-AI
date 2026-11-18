# Phase 4 Source Access Log

Audit date: 2026-11-17 (Asia/Kolkata). Credentials were loaded through `src/bharatair/config.py:get_xkdr_api_key()`. No credential value was printed or written to any artifact.

## XKDR authenticated API

Authentication succeeded. These API snapshots were retained under `data/phase4_audit/source_snapshot_20261117T000000Z/` with HTTP status, byte size, SHA-256 and retrieval time in `snapshot_manifest.json`:

| Endpoint | Result | SHA-256 |
|---|---:|---|
| `/v1/meta` | HTTP 200, 664 bytes | `b60be5899de15609ba4631e7b62240bd411d9f83eb421e2c68275715acbd0d09` |
| `/v1/stations?source=cpcb_caaqm` | HTTP 200, 553 station rows, 208,754 bytes | `811d16a5556d6e6eb74a7885fe19ec6c41a30cda0cbb8c2dce29ae720cddf7f7` |
| `/v1/parameters` | HTTP 200, 15 parameter rows, 2,291 bytes | `0c1dc853ab7f6a337e540b72231c6b9de635eb6da0e2e48d888a71a26d9633ad` |
| `/v1/files` | HTTP 200, 209 index records, 27,541 bytes | `7fd506983d804b540569ee19a5583aa28bccaedfdaa30836bcec51664d1d96e1` |

The export index says 196,521,834 readings and 409,568,028 compressed bytes in 207 monthly measurement files (2009-01 through 2026-03). This is the *whole* source export across networks and pollutants; it was not downloaded wholesale. The source describes hourly data, 558 stations and 15 pollutant parameters, with last publication 2026-09-30. The database documentation specifies naive IST timestamps, CPCB top-of-hour records, Embassy half-hour records, CC BY 4.0 attribution, and no gap filling or outlier removal. The current CPCB metadata has both city and state populated for 245 observed city/state pairs; 62 measured stations lack a state label and 29 lack both city and state, so their records remain in the station inventory but are not geographically guessed.

## CPCB CAAQM PM2.5 extracts

Only the filtered query `source=cpcb_caaqm&parameter=PM2.5&format=parquet` was retrieved, in calendar-year requests from 2009 through 2026-03-31. All 18 responses were HTTP 200 and `X-Truncated=false`. They contain 17,594,014 rows in 60,698,411 bytes total (about 14.5% of the full index byte size). Files are in `data/phase4_audit/raw_cpcb_pm25/yearly/`; the complete URL, query, response row count, byte size, timestamp and SHA-256 for each file are in `retrieval_manifest.json`.

| Year | PM2.5 rows | Year | PM2.5 rows | Year | PM2.5 rows |
|---:|---:|---:|---:|---:|---:|
| 2009 | 4,715 | 2015 | 148,059 | 2021 | 2,078,256 |
| 2010 | 6,027 | 2016 | 239,154 | 2022 | 2,485,808 |
| 2011 | 16,020 | 2017 | 329,228 | 2023 | 3,394,698 |
| 2012 | 30,701 | 2018 | 863,633 | 2024 | 3,892,007 |
| 2013 | 19,123 | 2019 | 1,348,911 | 2025 | 1,057,327 |
| 2014 | 16,840 | 2020 | 1,663,507 | 2026 through March | 0 |

The 2024 annual transfer (3,892,007 rows, 12,838,691 bytes) confirmed that year-bounded transfer is practical. No all-pollutant archive was downloaded. A separate January 2024 raw probe is retained in its own `month=01` folder and is **not** included in the annual totals or station audit.

The latest CPCB PM2.5 timestamp in returned observations is **2025-09-01 23:00 IST**. The entire 2026-01-01 through 2026-03-31 CPCB-filtered query was a valid empty Parquet response (0 rows, 197 bytes). Monthly file-index rows after 2025-09 exist, but they are not evidence of CPCB PM2.5 readings; they are excluded from this CPCB count.

## Official CPCB station register

Downloaded the [CPCB CCR All-India CAAQMS station register PDF](https://app.cpcbccr.com/ccr_docs/caaqms_list_All_India.pdf), 40,901 bytes, SHA-256 `72bd87631dffac40b29ebf111bae8fe5f773943734073b93007d18810f055513`. It contains 358 site-coded station rows in this snapshot and names operating agency, city and coordinates. Exact `site_NNNN` matching links 348 PM2.5-observed station IDs to an entry in this register. The current register snapshot is smaller than XKDR's current 553-station metadata list; 201 of the 549 PM2.5-observed IDs do not occur in this PDF snapshot. They remain in the inventory, retain XKDR metadata and are flagged as unverified against this register; they were not discarded.

The register identifies `site_1422` as **Dwarka-Sector 8, Delhi**, operator **DPCC**, at approximately 28.5710 N, 77.0719 E. CPCB's [CCR resources page](https://app.cpcbccr.com/ccr_docs) describes the list as a snapshot and directs users to the live portal. The 2015 [CAAQM transmission protocol](https://app.cpcbccr.com/ccr_docs/Protocol_CAAQM.pdf) describes 15-minute station transmissions. The observations actually returned by this XKDR PM2.5 extract are all on the hour. Treat the delivered series as hourly; do not infer that quarter-hour source records were retained.

## Embassy network, retained separately

To identify the origin of the small late-period file-index rows without mixing them into CPCB statistics, queried `/v1/stations?source=us_embassy` and a narrow Embassy-only PM2.5 range for 2026 Q1. These are stored in `data/phase4_audit/raw_us_embassy_separate/`, not in the CPCB station files or rankings. The Q1 response contained **4,047 rows from two station IDs** (`DS1010001`, US Embassy–New Delhi; `DS1010005`, US Embassy–Hyderabad), all at `:30`, from 2026-01-01 00:30 through 2026-03-27 23:30 IST. They are Embassy observations and are not eligible as CPCB extension data.

## Reproducibility and caveats

The filtered annual API workflow is repeatable using the documented endpoint, exact source/parameter/date filters and a personal key. It is suitable for a targeted bulk pull: 60.7 MB for the complete available CPCB PM2.5 history, versus 409.6 MB for every pollutant and network in the whole index. Keep the request manifest and source snapshots with every future retrieval, because the XKDR export can change between publications. XKDR states CC BY 4.0 and requests attribution to the India Air Quality Database/XKDR Forum and original sources (CPCB CAAQM; Embassy data via AirNow where applicable). It also warns that values are as received, preliminary and not warranted for regulatory or health decisions. Re-check current license terms and attribution at the time of republication.
