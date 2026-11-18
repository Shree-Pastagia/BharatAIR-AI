"""Page 8: Methodology & Sources — BharatAir Dashboard."""

import streamlit as st
from bharatair.dashboard.components.footer import render_footer


def render_page() -> None:
    """Render Methodology & Sources analytics page."""
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Methodology & Sources</h1>
            <div class="page-subtitle">
                Data Provenance, Quality Assurance Standards, and Mathematical Forecasting Formulations
            </div>
            <div class="badge-row">
                <span class="status-pill pill-verified">Scientific Documentation</span>
                <span class="status-pill pill-station">CPCB CAAQM Network</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### 1. Data Provenance & Authoritative Sourcing
        * **Regulatory Source:** Continuous Ambient Air Quality Monitoring (CAAQM) stations operated under the **Central Pollution Control Board (CPCB)** and the **Delhi Pollution Control Committee (DPCC)**.
        * **Ingestion Portal:** Authenticated monthly Parquet bulk repository maintained by the **XKDR Forum India Air Quality Database**.
        * **Benchmark Monitoring Station:** `site_1422` located at Dwarka Sector 8, New Delhi (28.5710° N, 77.0719° E), providing 63,178 verified hourly observations across 92 calendar months (February 2018 to September 2025).
        """
    )

    st.markdown(
        r"""
        ### 2. Quality Assurance & Zero-Imputation Protocol
        To ensure scientific validity and avoid introducing false signals into sequence models, BharatAir enforces strict quality controls:
        * **Zero Imputation:** Missing sensor periods are explicitly audited rather than synthetically filled. Imputing across multi-day outages fabricates unphysical atmospheric states and distorts machine learning training signals.
        * **True Physical Units:** All observations represent physical mass concentrations ($\mu\text{g/m}^3$) of fine particulate matter (PM2.5), avoiding lossy non-linear AQI conversions.
        * **Outlier Preservation:** Extreme values legitimately reach 500–900 $\mu\text{g/m}^3$ during northern Indian winter inversion events. Preserving verified peaks ensures models learn realistic crisis behavior.
        * **Data Hygiene:** The canonical dataset contains 0 negative values, 0 duplicate timestamp offsets, and 100% minute-aligned hourly readings.
        """
    )

    st.markdown(
        r"""
        ### 3. Chronological Train / Validation / Test Splitting
        To prevent lookahead bias and autocorrelation leakage in time series, all partitions are strictly chronological:

        $$\text{Total Observations: } 63,178 \text{ hours (2018-02-01 to 2025-09-01)}$$

        * **Train Partition (70%):** `2018-02-01 10:00:00` to `2023-03-22 11:00:00 IST` (44,224 observations).
        * **Validation Partition (15%):** `2023-03-22 12:00:00` to `2024-04-30 01:00:00 IST` (9,477 observations). Used for architecture comparisons and hyperparameter tuning.
        * **Test Partition (15%):** `2024-04-30 02:00:00` to `2025-09-01 23:00:00 IST` (Held out and locked).
        * **Train-Only Scaling:** Standardizers (StandardScaler) are fitted strictly on the train partition. Normalization statistics never incorporate validation or test data.
        """
    )

    st.markdown(
        r"""
        ### 4. Mathematical Modeling Formulations
        Let $y_t$ denote the observed PM2.5 concentration at hour $t$. For a given lookback window $L \in \{24, 48, 168\}$ and horizon $H \in \{1, 6, 12, 24\}$, the forecasting task estimates:

        $$\hat{y}_{t+H} = f(y_t, y_{t-1}, \dots, y_{t-L+1}; \theta)$$

        #### Evaluated Model Architectures
        1. **Baselines:**
           * *Persistence:* $\hat{y}_{t+H} = y_t$
           * *Seasonal Naive (24h):* $\hat{y}_{t+H} = y_{t+H-24}$
        2. **Traditional Machine Learning:**
           * *Linear Regression with Ridge Regularization:* $\hat{y} = X\beta$
           * *Random Forest Regressor:* 80 ensemble decision trees, maximum depth 14.
           * *XGBoost Regressor:* Gradient-boosted decision trees with histogram binning.
        3. **Deep Learning Architectures (PyTorch / CUDA):**
           * *LSTM:* Multi-layer recurrent neural network with input, forget, and output gating.
           * *GRU:* Gated recurrent units with update and reset gates.
           * *TCN:* Temporal Convolutional Network with causal dilated 1D convolutions and exponential receptive field expansion.
        """
    )

    st.markdown(
        r"""
        ### 5. Evaluation Metrics

        $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$

        $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$

        $$\text{MASE} = \frac{\text{MAE}}{\frac{1}{T-1} \sum_{t=2}^T |y_t - y_{t-1}|} \quad (\text{scaled against training random walk baseline } 14.60 \, \mu\text{g/m}^3)$$
        """
    )

    st.markdown(
        """
        ### 6. Scientific References
        1. Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change, Government of India. *Guidelines for Ambient Air Quality Monitoring (CAAQM Network)*.
        2. XKDR Forum. *India Air Quality Database: Open-Source High-Resolution Environmental Monitoring Data*.
        3. Bai, S., Kolter, J. Z., & Koltun, V. (2018). *An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling*. arXiv:1803.01271.
        4. Hyndman, R. J., & Koehler, A. B. (2006). *Another look at measures of forecast accuracy*. International Journal of Forecasting, 22(4), 679-688.
        """
    )

    render_footer()
