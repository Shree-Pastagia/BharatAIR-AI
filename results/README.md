# BharatAIR Empirical Results & Evaluation Benchmarks

This directory contains the central experimental benchmarks, evaluation metrics, sample model predictions, and publication-ready comparative figures generated across all 7 Indian megacities under BharatAIR's zero-leakage validation protocol.

---

## Directory Structure

```
results/
├── README.md                              # This document
│
├── metrics/                               # Validated evaluation metrics & ledgers
│   ├── model_leaderboard_benchmark.csv     # Architecture leaderboard (XGBoost, RF, TCN, GRU, LSTM, Linear)
│   ├── regional_airshed_champions_exp_b.csv# Experiment B winning models per megacity across horizons
│   ├── station_specific_champions_exp_a.csv# Experiment A winning models across all 107 CPCB stations
│   └── window_eligibility_by_split.csv    # Temporal train/val/test window integrity ledger
│
├── predictions/                           # Ground-truth vs AI prediction logs
│   └── validation_forecast_sample.csv     # Side-by-side sensor actuals vs +1h to +24h AI forecasts
│
└── plots/                                 # 300 DPI publication-grade figures
    ├── model_architecture_benchmark.png   # Head-to-head MAE & RMSE across all 6 architectures
    ├── horizon_error_growth_curve.png     # Horizon decision boundary: where Deep Learning beats classical ML
    └── cpcb_sensor_vs_ai_forecast.png     # 72-hour continuous sensor trajectory vs AI forecast curve
```

---

## 1. Key Performance Metrics (`metrics/`)

### Architecture Leaderboard (Experiment B Regional Pooling)
*Evaluated across 1,008 models on an NVIDIA GeForce RTX 4060 Laptop GPU (CUDA 12.6, PyTorch 2.14)*:

| Model Architecture | Model Family | Median MAE ($\mu\text{g/m}^3$) | Median RMSE ($\mu\text{g/m}^3$) | Mean Train Time | Best Operational Horizon |
|---|---|---|---|---|---|
| **Random Forest** | Traditional ML | **10.56** | 27.05 | 77.2s | **+1h** Immediate persistence warning |
| **XGBoost** | Traditional ML | **10.56** | 27.18 | **60.4s** | **+1h** Fast edge deployment |
| **TCN (Temporal ConvNet)** | Deep Sequence | **10.77** | **26.55** | 682.3s | **+24h** Multi-day synoptic weather fronts |
| **GRU** | Deep Recurrent | 11.12 | 26.78 | 722.9s | **+6h** Intraday boundary layer tracking |
| **Linear Regression** | Linear Baseline | 11.26 | 27.24 | **18.7s** | Linear baseline check |
| **LSTM** | Deep Recurrent | 11.27 | 26.85 | 674.1s | **+24h** Weekly diurnal rhythm ($L=168\text{h}$) |

---

## 2. Core Scientific Finding: The Horizon Decision Boundary (`plots/`)

1. **Near-Term (+1 Hour)**: Local autoregressive sensor persistence and microclimate topography dominate immediate changes. Traditional tree ensembles (Random Forest & XGBoost) achieve the lowest error ($\text{MAE} \pm 3.5\text{ to }14.6\text{ }\mu\text{g/m}^3$).
2. **Long-Horizon (+6h to +24 Hours)**: Local autoregression rapidly degrades as meteorological shifts occur. Deep Sequence Models (**TCN** with $L=168\text{h}$ weekly lookbacks) dominate, achieving the lowest overall RMSE ($26.55\text{ }\mu\text{g/m}^3$) by capturing synoptic weather transitions, boundary-layer height compression, and weekly traffic rhythms.

---

## 3. Interactive Exploration

For interactive time-series scrubbing, real-time government telemetry streaming, and 3D geospatial station exploration, launch the React frontend:
```bash
cd BharatAIR_Web
npm run build
npx vite preview --port 4173 --host
```
Open **`http://localhost:4173/`** to explore the live dashboard.
