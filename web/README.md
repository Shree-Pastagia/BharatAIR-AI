# BharatAIR Web App 🌬️🇮🇳

> **National Air Quality AI Forecasting Platform**
> A high-performance, interactive dashboard translating 7 years of Central Pollution Control Board (CPCB) telemetry and thousands of trained AI models into intuitive, hyper-local PM2.5 forecasts.

---

## Features

- **Instant Comprehension (Apple Weather Style)**: Big, clear PM2.5 readouts with official Indian National Air Quality Index (NAQI) color scales and plain-English health guidance.
- **Predictive Horizon Scrubber**: Interactive toggles for **+1h, +6h, +12h, and +24h** forecasts with real-time error margins (MAE).
- **Ground Truth vs. AI Forecast Charts**: High-frequency interactive time-series curves comparing actual CPCB sensor telemetry against deep sequence models (TCN) and classical ensembles (XGBoost/Random Forest).
- **Model Duel & Leaderboard**: Head-to-head empirical comparisons across the 4 core presentation architectures (Linear Regression, Random Forest, XGBoost, and TCN) with training times and error metrics.
- **Scientific Audit**: Transparent documentation of chronological train/val splits and zero-leakage cryptographic guarantees.

---

## Local Development

```bash
# 1. Install dependencies
npm install

# 2. Start development server
npm run dev
```

App will run locally at `http://localhost:5173/`.

---

## Deploy to Vercel (One-Click)

### Option 1: Via Vercel CLI
```bash
npx vercel
```

### Option 2: Via GitHub & Vercel Dashboard
1. Push this folder to a GitHub repository.
2. In [Vercel](https://vercel.com/), click **Add New Project** and import the repository.
3. Framework Preset: **Vite**
4. Click **Deploy**. Your live app will be accessible at `https://bharatair.vercel.app`!
