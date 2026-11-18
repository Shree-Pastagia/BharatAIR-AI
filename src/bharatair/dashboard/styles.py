"""Enterprise data analytics dashboard styling for BharatAir.

Modern dark-navy aesthetic, clean card surfaces, glowing teal/cyan accents,
and responsive analytics layout.
"""

import streamlit as st


def apply_custom_styles() -> None:
    """Inject polished custom CSS styling for modern analytics dashboard UI."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        /* Root Canvas: Modern Dark Navy */
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background-color: #0B1120 !important;
            color: #F8FAFC !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        /* Container padding */
        .block-container {
            max-width: 1440px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 3.0rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* Sidebar: Dark Charcoal Slate */
        [data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        [data-testid="stSidebar"] * {
            color: #E2E8F0 !important;
        }

        /* Sidebar Navigation links */
        [data-testid="stSidebarNav"] a {
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 3px;
            transition: all 0.15s ease-in-out;
        }

        [data-testid="stSidebarNav"] a:hover {
            background-color: #1E293B !important;
            color: #38BDF8 !important;
        }

        [data-testid="stSidebarNav"] [aria-selected="true"] {
            background-color: #0D9488 !important;
            color: #FFFFFF !important;
            font-weight: 600;
        }

        /* Top Page Header */
        .page-header {
            margin-bottom: 20px;
        }

        .page-title {
            font-size: 1.95rem;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.025em;
            margin: 0;
            line-height: 1.2;
        }

        .page-subtitle {
            font-size: 0.95rem;
            color: #94A3B8;
            margin-top: 4px;
            margin-bottom: 14px;
            font-weight: 400;
        }

        /* Status Badges */
        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.725rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }

        .pill-verified {
            background: rgba(16, 185, 129, 0.12);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.28);
        }

        .pill-station {
            background: rgba(56, 189, 248, 0.12);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.28);
        }

        .pill-benchmark {
            background: rgba(168, 85, 247, 0.12);
            color: #C084FC;
            border: 1px solid rgba(168, 85, 247, 0.28);
        }

        /* Analytics KPI Card */
        .kpi-card {
            background-color: #1E293B;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
            transition: border-color 0.15s ease, transform 0.15s ease;
        }

        .kpi-card:hover {
            border-color: rgba(56, 189, 248, 0.35);
        }

        .kpi-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }

        .kpi-value {
            font-size: 1.95rem;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.03em;
            line-height: 1.15;
        }

        .kpi-subtitle {
            font-size: 0.775rem;
            color: #2DD4BF;
            font-weight: 500;
            margin-top: 4px;
        }

        /* Analytics Content Panel */
        .content-panel {
            background-color: #1E293B;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }

        .panel-heading {
            font-size: 1.1rem;
            font-weight: 700;
            color: #FFFFFF;
            margin-top: 0;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Analytical Insight Callout */
        .insight-callout {
            background: linear-gradient(135deg, rgba(13, 148, 136, 0.12) 0%, rgba(2, 132, 199, 0.08) 100%);
            border-left: 4px solid #14B8A6;
            border-radius: 4px 10px 10px 4px;
            padding: 14px 18px;
            margin-top: 14px;
            margin-bottom: 14px;
            font-size: 0.875rem;
            color: #E2E8F0;
            line-height: 1.55;
        }

        .insight-callout strong {
            color: #FFFFFF;
        }

        /* Clean Dashboard Footer */
        .app-footer {
            margin-top: 40px;
            padding-top: 18px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 0.775rem;
            color: #64748B;
            text-align: center;
            line-height: 1.6;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .stTabs [data-baseweb="tab"] {
            height: 40px;
            font-size: 0.875rem;
            font-weight: 500;
            color: #94A3B8;
            padding: 0 14px;
            border: none;
        }

        .stTabs [aria-selected="true"] {
            color: #2DD4BF !important;
            border-bottom: 2px solid #2DD4BF !important;
            font-weight: 600;
        }

        /* Controls overrides */
        .stSelectbox label, .stRadio label, .stSlider label {
            color: #CBD5E1 !important;
            font-size: 0.825rem !important;
            font-weight: 500;
        }

        /* Buttons */
        .stButton button {
            background-color: #1E293B !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            transition: all 0.15s ease !important;
        }

        .stButton button:hover {
            background-color: #0D9488 !important;
            border-color: #2DD4BF !important;
            color: #FFFFFF !important;
        }

        /* Dataframe table */
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            background-color: #1E293B;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background-color: #1E293B !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
            color: #E2E8F0 !important;
            font-size: 0.875rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
