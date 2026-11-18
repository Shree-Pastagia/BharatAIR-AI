"""Chapter 3: The Machine Learning Approach — BharatAir Presentation."""

import streamlit as st
from bharatair.dashboard.components.presentation_nav import render_chapter_buttons, render_presentation_header


def render_page(chapter_idx: int = 2) -> None:
    """Render Chapter 3: Teaching Machines to Understand Pollution."""
    render_presentation_header(chapter_idx)

    st.markdown(
        """
        <div class="chapter-header">
            <h2 class="chapter-headline">Teaching Machines to Understand Pollution</h2>
        </div>
        <p class="chapter-desc">
            Can machine learning models learn the complex, non-linear dynamics of Delhi's atmosphere?
            We framed air pollution forecasting as an autoregressive sequence prediction problem.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Attractive Visual Pipeline
    st.markdown("### The BharatAir Machine Learning Pipeline")
    st.markdown(
        """
        <div class="pipeline-flow">
            <div class="pipeline-step">
                <div class="pipeline-step-num">Step 1</div>
                <div class="pipeline-step-name">CPCB Observations</div>
                <div class="pipeline-step-sub">63,178 raw hourly points (Dwarka Sector 8)</div>
            </div>
            <div class="pipeline-arrow">➔</div>
            <div class="pipeline-step">
                <div class="pipeline-step-num">Step 2</div>
                <div class="pipeline-step-name">Sequence Windowing</div>
                <div class="pipeline-step-sub">L ∈ {24h, 48h, 168h} Lookbacks, Zero Imputation</div>
            </div>
            <div class="pipeline-arrow">➔</div>
            <div class="pipeline-step">
                <div class="pipeline-step-num">Step 3</div>
                <div class="pipeline-step-name">Model Training</div>
                <div class="pipeline-step-sub">72 ML/DL Candidates + 8 Baselines on CUDA GPU</div>
            </div>
            <div class="pipeline-arrow">➔</div>
            <div class="pipeline-step">
                <div class="pipeline-step-num">Step 4</div>
                <div class="pipeline-step-name">Validation Benchmark</div>
                <div class="pipeline-step-sub">15% Chronological Split (9,477 Target Hours)</div>
            </div>
            <div class="pipeline-arrow">➔</div>
            <div class="pipeline-step">
                <div class="pipeline-step-num">Step 5</div>
                <div class="pipeline-step-name">Horizon Discovery</div>
                <div class="pipeline-step-sub">Evaluation at +1h, +6h, +12h, and +24h</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Autoregressive Task Formulation
    st.markdown("### The Forecasting Formulation: Looking Back to See Ahead")

    col_form1, col_form2 = st.columns([1.3, 1])

    with col_form1:
        st.markdown(
            """
            <div class="pres-card">
                <h4 style="color: #38BDF8; margin-top: 0; font-size: 1.1rem;">Predicting Future Pollution: ŷ(t + H)</h4>
                <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6;">
                    Given a sequence of historical PM2.5 readings <strong>[y(t), y(t-1), ..., y(t - L + 1)]</strong> over
                    a lookback window of <strong>L hours</strong>, the model must predict the single ambient concentration
                    at <strong>H hours in the future</strong>.
                </p>
                <div style="background: rgba(10, 15, 29, 0.6); padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); margin: 12px 0;">
                    <code style="color: #2DD4BF; font-size: 0.95rem;">ŷ_{t+H} = f(y_t, y_{t-1}, ..., y_{t-L+1} ; θ)</code>
                </div>
                <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.5; margin-bottom: 0;">
                    Every window requires 100% of input hours and the target hour to be observed. Windows overlapping sensor
                    outages (≥24h missing) are excluded to ensure training continuity without imputation artifacts.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_form2:
        st.markdown(
            """
            <div class="pres-card-highlight">
                <h4 style="color: #2DD4BF; margin-top: 0; font-size: 1.1rem;">Experiment Matrix Dimensions</h4>
                <div style="margin-bottom: 14px;">
                    <span style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Input Lookback Windows (L)</span>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-top: 4px;">
                        • 24 Hours <span style="font-weight: 400; color: #94A3B8;">(1 Day of Diurnal Context)</span><br>
                        • 48 Hours <span style="font-weight: 400; color: #94A3B8;">(2 Days of Trend Memory)</span><br>
                        • 168 Hours <span style="font-weight: 400; color: #94A3B8;">(1 Full Week Synoptic Pattern)</span>
                    </div>
                </div>
                <div>
                    <span style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Forecast Horizons (H)</span>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-top: 4px;">
                        • +1 Hour <span style="font-weight: 400; color: #94A3B8;">(Immediate Reactive)</span><br>
                        • +6 Hours <span style="font-weight: 400; color: #94A3B8;">(Short-Term Advisory)</span><br>
                        • +12 Hours <span style="font-weight: 400; color: #94A3B8;">(Half-Day Commute)</span><br>
                        • +24 Hours <span style="font-weight: 400; color: #94A3B8;">(Full Next-Day Alert)</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # The 3 Model Families
    st.markdown("### The Three Model Families Under Evaluation")

    c_b, c_ml, c_dl = st.columns(3)

    with c_b:
        st.markdown(
            """
            <div class="pres-card" style="height: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="badge-pill-amber">Baselines</span>
                    <span style="color: #94A3B8; font-size: 0.75rem;">8 Evaluations</span>
                </div>
                <h4 style="color: #FFFFFF; margin: 4px 0 10px 0;">Naive Benchmarks</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.5;">
                    • <strong>Persistence:</strong> Assumes tomorrow will be identical to this hour (<code>ŷ_{t+H} = y_t</code>).<br><br>
                    • <strong>Seasonal Naive (24h):</strong> Assumes tomorrow's 9 AM will match today's 9 AM (<code>ŷ_{t+H} = y_{t+H-24}</code>).<br><br>
                    <em>Any serious ML model must beat these simple heuristics!</em>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_ml:
        st.markdown(
            """
            <div class="pres-card" style="height: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="badge-pill-cyan">Traditional ML</span>
                    <span style="color: #94A3B8; font-size: 0.75rem;">36 Candidates</span>
                </div>
                <h4 style="color: #FFFFFF; margin: 4px 0 10px 0;">Linear & Tree Ensembles</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.5;">
                    • <strong>Linear Regression (Ridge):</strong> Fast L2-regularized linear combination of lag features.<br><br>
                    • <strong>Random Forest:</strong> 80 decision trees with bootstrap aggregation and feature subsampling.<br><br>
                    • <strong>XGBoost:</strong> Scaled gradient-boosted decision trees with histogram binning.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_dl:
        st.markdown(
            """
            <div class="pres-card" style="height: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="badge-pill-teal">Deep Learning</span>
                    <span style="color: #94A3B8; font-size: 0.75rem;">36 Candidates</span>
                </div>
                <h4 style="color: #FFFFFF; margin: 4px 0 10px 0;">Neural Sequence Models</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.5;">
                    • <strong>LSTM:</strong> Multi-layer recurrent network with forget, input, and output gating mechanisms.<br><br>
                    • <strong>GRU:</strong> Streamlined recurrent architecture with reset and update gates.<br><br>
                    • <strong>TCN:</strong> Dilated causal 1D convolutions with exponential receptive fields.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Expandable Technical Deep-Dive for Interested Viewers/Professors
    with st.expander("🎓 Expand for Technical Details: Training Protocol & GPU Telemetry", expanded=False):
        st.markdown(
            """
            * **Strict Temporal Splitting:**
              - *Train Partition (70%):* `2018-02-01 10:00:00` to `2023-03-22 11:00:00 IST` (44,224 observations).
              - *Validation Partition (15%):* `2023-03-22 12:00:00` to `2024-04-30 01:00:00 IST` (9,477 observations).
              - *Test Partition (15%):* `2024-04-30 02:00:00` to `2025-09-01 23:00:00 IST` (**Locked & Unaccessed**).
            * **Distribution Isolation:** Feature scalers (StandardScaler) are fitted *strictly* on training partition sequences; validation and test splits are never seen during normalization.
            * **Hardware Environment:** Trained on dedicated NVIDIA GeForce RTX 4060 Laptop GPU with PyTorch and CUDA 12.6.
            * **Candidate Verification:** Every candidate checkpoint is saved with an isolated SHA-256 integrity hash and exact parameter manifest.
            """
        )

    # Bottom navigation
    render_chapter_buttons(chapter_idx)

