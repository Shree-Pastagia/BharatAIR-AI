# BharatAIR — National Air Quality AI Forecasting Platform

<p align="center">
  <img src="logo.png" width="180" alt="BharatAIR Logo" />
</p>

> **Empirical Environmental Data Science & Deep Sequence Forecasting Across 7 Indian Megacities**  
> Benchmarked on authentic Central Pollution Control Board (CPCB) continuous ambient air quality monitoring (CAAQMS) sensor telemetry.

---

## Executive Summary

**BharatAIR** is a full-stack, presentation-ready air quality intelligence and deep learning forecasting platform. Rather than relying on synthetic data or black-box assumptions, BharatAIR evaluates **over 6,400 empirical model fits** across 107 continuous regulatory monitoring stations in **7 Indian megacities**:
* **Delhi** (37 stations)
* **Mumbai** (29 stations)
* **Hyderabad** (10 stations)
* **Bengaluru** (11 stations)
* **Ahmedabad** (7 stations)
* **Kolkata** (7 stations)
* **Chennai** (6 stations)

---

## Core Scientific Breakthrough: The Two Paradigms

BharatAIR systematically benchmarked two opposing machine learning paradigms on an **NVIDIA GeForce RTX 4060 Laptop GPU** (CUDA 12.6, PyTorch 2.14) under a strict zero-leakage cryptographic policy:

### 1. Paradigm A: Localized Station-Specific Models (Experiment A)
* **5,466 model fits** trained independently per station.
* **Near-Term Dominance (+1h)**: Autoregressive classical ML (**Random Forest**, median MAE $\pm 3.5\text{ to }14.6\text{ }\mu\text{g/m}^3$) consistently outperforms deep learning because localized 60-minute sensor persistence and immediate microclimate topography dominate immediate changes.

### 2. Paradigm B: Regional Airshed Multi-City Pooling (Experiment B)
* **1,008 candidate models** pooled across multi-station urban airsheds ($L \in \{24, 48, 168\}\text{h}$, $H \in \{1, 6, 12, 24\}\text{h}$).
* **Long-Horizon Dominance (+6h to +24h)**: Deep Sequence Architecture (**Temporal Convolutional Network / TCN**) with a **7-day lookback ($L=168\text{h}$)** achieves the lowest overall RMSE ($26.55\text{ }\mu\text{g/m}^3$). It successfully resolves multi-day synoptic weather fronts, nocturnal boundary-layer height compression, and diurnal traffic cycles.

---

## The 4 Core Machine Learning Architectures (Classroom Presentation Guide)

For academic clarity, conceptual rigor, and clean presentation in class, BharatAIR highlights **4 primary machine learning architectures** representing four fundamentally distinct algorithmic paradigms:

| # | Architecture | Algorithmic Paradigm | Why It's Used in Air Quality | Primary Strength |
|---|---|---|---|---|
| **1** | **Linear Regression (OLS)** | Parametric Linear Baseline | Transparent mathematical baseline with zero black-box obscurity. Fits in milliseconds and sets the standard for linear variance. | Baseline transparency |
| **2** | **Random Forest** | Non-Linear Bagging Ensemble | 100 parallel randomized decision trees. Captures localized autoregressive inertia without overfitting sudden sensor noise or spikes. | **+1h Near-Term Champion** ($\pm 14.6\text{ }\mu\text{g/m}^3$) |
| **3** | **XGBoost** | Gradient Boosting (Residual Learning) | Sequentially minimizes loss gradients with histogram acceleration (`hist`). Excellent middle-ground between speed and mid-range precision. | **+6h / +12h Transition** ($\pm 34.2\text{ }\mu\text{g/m}^3$) |
| **4** | **TCN (Temporal ConvNet)** | Deep Causal 1D Convolution | Dilated causal convolutions ($d \in \{1, 2, 4, 8, 16, 32\}$) spanning a 7-day receptive field ($L=168\text{h}$) to capture nocturnal boundary inversions. | **+24h Full-Day Champion** ($\pm 36.2\text{ }\mu\text{g/m}^3$, **-43% vs Naive**) |

> **Note on Backend vs. Frontend**: The web dashboard and public documentation intentionally present these **4 clean, easily explainable models** for evaluators and students. Additional experimental architectures remain safely archived in the backend Python codebase (`src/bharatair/models/`).

---

## Repository Architecture

```
BharatAIR/
├── README.md                          # Master project documentation
├── requirements.txt                    # Python dependencies
├── .env                                # Local environment keys (CPCB/data.gov.in)
├── app.py                              # Streamlit presentation dashboard
│
├── scripts/                            # Operational & automation CLI tools
│   ├── poll_live_cpcb_daemon.py        # Automated hourly background poller for live CPCB data
│   ├── fetch_live_cpcb.py              # Instantaneous CPCB snapshot fetcher
│   ├── sync_experiments_to_web.py      # Compiles verified model metrics to web JSON
│   ├── monitor_gpu_training.py         # Real-time CUDA training progress terminal
│   ├── rolling_accuracy_logger.py      # Tracks ground-truth vs 24h prior forecasts
│   ├── build_multiyear_timeseries.py   # Compiles 2018–2024 longitudinal dataset
│   ├── build_historical_coverage.py    # Audits station sensor availability
│   └── pipeline_archive/               # Historical phase pipeline scripts
│
├── runs/                               # Audited training runs & checkpoints
│   ├── phase5_B_primary_cuda_.../      # Experiment B: 1,008 Regional Multi-City Models
│   ├── phase5_A_primary_cuda_.../      # Experiment A: 5,466 Station-Specific Models
│   └── phase3_cuda_full_.../           # Phase 3: Single-Station Dwarka Baseline
│
├── reports/                            # Technical reports & audit summaries
│   ├── audit_data/                     # Station cohort, feasibility, & window CSVs
│   ├── design_reports/                 # Methodology & split window audit documents
│   └── screenshots/                    # UI captures & validation curves
│
├── src/bharatair/                      # Core Python data & modeling package
│   ├── data/                           # Ingestion, validation, gap audits
│   ├── features/                       # Windowing, standard scaling (zero test leakage)
│   ├── models/                         # 4 Core Architectures: Linear Regression, Random Forest, XGBoost, TCN (plus backend extensions)
│   ├── phase5/                         # Multi-station batch training engine
│   └── dashboard/                      # Presentation components & charts
│
└── tests/                              # Automated pytest suite (38 passing tests)
```

### Web Application (`web/`)
Located directly in `web/`, the interactive production web frontend features:
* **Forecast Studio**: Interactive station map, Apple Weather-style NAQI gauge, and multi-year retrospective time scrubber (2018–2024).
* **Live 2026 Forecaster**: Real-time government telemetry synchronization via `data.gov.in`, displaying continuous 72-hour chronological sensor-to-AI flows.
* **Research & Paradigms**: Side-by-side scientific comparison of Experiment A vs. Experiment B with 7-megacity interactive champion selectors.
* **Model Duel & Leaderboard**: Empirical head-to-head metrics comparing training times, MAE, and RMSE across model families.
* **Scientific Audit**: Cryptographic guarantees proving locked test splits and zero temporal leakage.

---

## Quickstart

### 1. Launch Web Application
```bash
cd web
npm install
npm run build
npx vite preview --port 4173 --host
```
Open **`http://localhost:4173/`** in your browser.

### 2. Poll Live Government Telemetry (Continuous Daemon)
```bash
python scripts/poll_live_cpcb_daemon.py
```

### 3. Automated Cloud Sync (GitHub Actions)
The repository includes an automated GitHub Actions cron workflow ([`.github/workflows/sync_live_cpcb.yml`](.github/workflows/sync_live_cpcb.yml)) that polls CPCB once every hour, updates `web/public/data/live_cpcb_telemetry.json`, and commits the latest observations to GitHub automatically.

### 4. Run Verification Tests
```bash
python -m pytest tests/
```
