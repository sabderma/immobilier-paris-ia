from __future__ import annotations

import streamlit as st


def styles() -> None:
    st.markdown(
        """
        <style>
            .stApp,
            [data-testid="stAppViewContainer"] {
                background: #ffffff;
                color: #111827;
            }
            [data-testid="stHeader"] {
                display: none;
            }
            [data-testid="stElementContainer"]:has(style) {
                display: none;
            }
            .block-container {
                max-width: none;
                width: 100%;
                box-sizing: border-box;
                overflow-x: hidden;
                padding: 2rem 1.25rem 1rem;
            }
            [data-testid="stWidgetLabel"] p,
            [data-testid="stWidgetLabel"] label,
            [data-testid="stWidgetLabel"] span {
                color: #111827 !important;
                font-weight: 700 !important;
                opacity: 1 !important;
            }
            [data-baseweb="select"] > div {
                background: #ffffff !important;
                border-color: #cbd5e1 !important;
                color: #111827 !important;
            }
            [data-baseweb="select"] span,
            [data-baseweb="select"] input,
            [data-baseweb="select"] svg {
                color: #111827 !important;
                fill: #111827 !important;
            }
            [data-testid="stForm"] {
                border: 1px solid #e5e7eb;
                border-radius: 0.75rem;
                background: #ffffff;
                padding: 1rem 1.15rem 0.95rem;
                margin-top: 0.75rem;
            }
            [data-testid="stNumberInput"] [data-baseweb="input"],
            [data-testid="stNumberInput"] [data-baseweb="base-input"] {
                background: #ffffff !important;
                border-color: #cbd5e1 !important;
                color: #111827 !important;
            }
            [data-testid="stTextInput"] [data-baseweb="input"],
            [data-testid="stTextInput"] [data-baseweb="base-input"] {
                background: #ffffff !important;
                border-color: #cbd5e1 !important;
                color: #111827 !important;
            }
            [data-testid="stNumberInput"] input {
                background: #ffffff !important;
                color: #111827 !important;
                -webkit-text-fill-color: #111827 !important;
            }
            [data-testid="stTextInput"] input {
                background: #ffffff !important;
                color: #111827 !important;
                -webkit-text-fill-color: #111827 !important;
            }
            [data-testid="stTextInput"] input::placeholder {
                color: #94a3b8 !important;
                -webkit-text-fill-color: #94a3b8 !important;
            }
            [data-testid="stNumberInput"] button {
                background: #ffffff !important;
                border-color: #cbd5e1 !important;
                color: #111827 !important;
            }
            [data-testid="stNumberInput"] button svg,
            [data-testid="stNumberInput"] button span {
                color: #111827 !important;
                fill: #111827 !important;
            }
            [data-testid="stFormSubmitButton"] button {
                background: #e11d48 !important;
                border: 1px solid #e11d48 !important;
                border-radius: 0.5rem !important;
                color: #ffffff !important;
                font-weight: 800 !important;
                padding: 0.65rem 1rem !important;
            }
            [data-testid="stFormSubmitButton"] button:hover {
                background: #be123c !important;
                border-color: #be123c !important;
                color: #ffffff !important;
            }
            [data-testid="stFormSubmitButton"] button p,
            [data-testid="stFormSubmitButton"] button span {
                color: #ffffff !important;
                opacity: 1 !important;
            }
            [data-testid="stButtonGroup"] {
                width: 100%;
                margin: 0 0 1rem;
            }
            [data-testid="stButtonGroup"] [data-baseweb="button-group"] {
                display: flex;
                width: 100%;
                gap: 0.55rem;
                background: transparent;
                border: none;
            }
            [data-testid="stButtonGroup"] button {
                flex: 1 1 0;
                min-height: 64px;
                justify-content: center;
                padding: 0.75rem 0.65rem !important;
                border: 1px solid #e5e7eb !important;
                border-radius: 0.75rem !important;
                background: #f8fafc !important;
                color: #475569 !important;
                font-weight: 700 !important;
                opacity: 1 !important;
                white-space: normal !important;
            }
            [data-testid="stButtonGroup"] button p {
                color: #475569 !important;
                font-size: 0.98rem !important;
                font-weight: 800 !important;
                line-height: 1.2 !important;
                opacity: 1 !important;
            }
            [data-testid="stButtonGroup"] [data-testid="stBaseButton-segmented_controlActive"] {
                background: #fff1f2 !important;
                border-color: #fb7185 !important;
                box-shadow: 0 8px 22px rgba(225, 29, 72, 0.12);
                color: #e11d48 !important;
            }
            [data-testid="stButtonGroup"] [data-testid="stBaseButton-segmented_controlActive"] p {
                color: #e11d48 !important;
            }
            [data-testid="stDownloadButton"] button {
                background: #f3f4f6 !important;
                border: 1px solid #f3f4f6 !important;
                border-radius: 0.45rem !important;
                color: #111827 !important;
                font-weight: 500 !important;
                padding: 0.6rem 0.9rem !important;
            }
            [data-testid="stDownloadButton"] button p,
            [data-testid="stDownloadButton"] button span {
                color: #111827 !important;
                opacity: 1 !important;
            }
            [data-testid="stSlider"] [role="slider"] {
                background: #ef4444 !important;
                border-color: #ef4444 !important;
            }
            [data-testid="stSlider"] [data-testid="stTickBar"] div {
                color: #111827 !important;
            }
            .leaflet-popup-content {
                color: #111827;
                font-size: 0.9rem;
                line-height: 1.45;
            }
            .sale-popup-title {
                display: block;
                font-weight: 800;
                margin-bottom: 0.25rem;
            }
            .sale-popup-row {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                min-width: 165px;
            }
            .sale-popup-label {
                color: #475569;
                font-weight: 650;
            }
            .sale-popup-value {
                color: #111827;
                font-weight: 750;
                text-align: right;
            }
            .breadcrumb { color: #64748b; font-size: 0.88rem; margin-bottom: 0.45rem; }
            .section-title {
                color: #374151;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }
            .city-title {
                color: #111827;
                font-size: 2rem;
                font-weight: 750;
                margin: 0.15rem 0 0.9rem;
            }
            .metric-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
                border-top: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
                padding: 1rem 0;
                margin-bottom: 0.8rem;
            }
            .metric-label { color: #374151; font-size: 0.84rem; font-weight: 650; }
            .metric-value { color: #111827; font-size: 1.7rem; font-weight: 750; }
            .listing-metric-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.9rem;
                border-top: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
                padding: 1rem 0;
                margin-bottom: 0.8rem;
            }
            .listing-date {
                color: #111827;
                font-size: 1.05rem;
                font-weight: 800;
                margin-top: 0.25rem;
            }
            .listing-panel-title {
                color: #111827;
                font-size: 1.2rem;
                font-weight: 850;
                margin: 0 0 0.75rem;
            }
            .listing-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.85rem;
            }
            .listing-pagination-info {
                color: #475569;
                font-size: 0.9rem;
                font-weight: 750;
                padding: 0.55rem 0;
                text-align: center;
            }
            .st-key-annonces_page_precedente button,
            .st-key-annonces_page_suivante button {
                background: #ffffff !important;
                border: 1px solid #fb7185 !important;
                color: #be123c !important;
                font-weight: 800 !important;
            }
            .st-key-annonces_page_precedente button p,
            .st-key-annonces_page_precedente button span,
            .st-key-annonces_page_suivante button p,
            .st-key-annonces_page_suivante button span {
                color: #be123c !important;
                opacity: 1 !important;
            }
            .st-key-annonces_page_precedente button:hover,
            .st-key-annonces_page_suivante button:hover {
                background: #fff1f2 !important;
                border-color: #e11d48 !important;
            }
            .st-key-annonces_page_precedente button:disabled,
            .st-key-annonces_page_suivante button:disabled {
                background: #f8fafc !important;
                border-color: #e2e8f0 !important;
            }
            .st-key-annonces_page_precedente button:disabled p,
            .st-key-annonces_page_precedente button:disabled span,
            .st-key-annonces_page_suivante button:disabled p,
            .st-key-annonces_page_suivante button:disabled span {
                color: #94a3b8 !important;
            }
            .listing-card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-top: 3px solid #fb7185;
                border-radius: 0.75rem;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
                padding: 1rem;
            }
            .listing-card-top {
                align-items: center;
                display: flex;
                justify-content: space-between;
                gap: 0.5rem;
            }
            .listing-source {
                background: #fff1f2;
                border: 1px solid #fecdd3;
                border-radius: 999px;
                color: #be123c;
                font-size: 0.72rem;
                font-weight: 850;
                letter-spacing: 0.035em;
                padding: 0.25rem 0.55rem;
                text-transform: uppercase;
            }
            .listing-date-small {
                color: #94a3b8;
                font-size: 0.76rem;
                font-weight: 650;
            }
            .listing-card-price {
                color: #111827;
                font-size: 1.55rem;
                font-weight: 850;
                margin-top: 0.8rem;
            }
            .listing-card-location {
                color: #475569;
                font-size: 0.88rem;
                font-weight: 700;
                margin-top: 0.15rem;
            }
            .listing-card-details {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.55rem;
                border-top: 1px solid #eef2f7;
                color: #64748b;
                font-size: 0.78rem;
                margin-top: 0.85rem;
                padding-top: 0.75rem;
            }
            .listing-card-details span:last-child {
                grid-column: 1 / -1;
            }
            .listing-card-details strong {
                color: #111827;
                display: block;
                font-size: 0.88rem;
                font-weight: 800;
            }
            [data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 0.6rem;
                padding: 0.85rem 0.95rem;
            }
            [data-testid="stMetric"] label,
            [data-testid="stMetric"] label p,
            [data-testid="stMetricLabel"],
            [data-testid="stMetricLabel"] p {
                color: #374151 !important;
                font-weight: 750 !important;
                opacity: 1 !important;
            }
            [data-testid="stMetricValue"],
            [data-testid="stMetricValue"] div,
            [data-testid="stMetricValue"] p {
                color: #111827 !important;
                font-weight: 800 !important;
                opacity: 1 !important;
            }
            .scope-note { color: #64748b; font-size: 0.82rem; margin-bottom: 0.9rem; }
            .chart-title {
                color: #111827;
                font-size: 0.95rem;
                font-weight: 750;
                margin: 0.8rem 0 0.15rem;
            }
            .map-note {
                color: #374151;
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 0.45rem;
                padding: 0.55rem 0.75rem;
                margin-top: 0.45rem;
                font-size: 0.86rem;
            }
            .info-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 1rem;
                font-size: 0.94rem;
            }
            .info-table th {
                background: #f8fafc;
                border-bottom: 1px solid #e5e7eb;
                color: #374151;
                font-weight: 800;
                padding: 0.7rem 0.8rem;
                text-align: left;
            }
            .info-table td {
                border-bottom: 1px solid #eef2f7;
                color: #111827;
                padding: 0.68rem 0.8rem;
            }
            .info-table td:last-child {
                font-weight: 800;
            }
            .prediction-result {
                border: 1px solid #fecdd3;
                border-radius: 0.75rem;
                background: #fff1f2;
                padding: 1.1rem 1.25rem;
                margin-top: 1rem;
            }
            .prediction-label {
                color: #9f1239;
                font-size: 0.86rem;
                font-weight: 800;
                text-transform: uppercase;
            }
            .prediction-price {
                color: #111827;
                font-size: 2.15rem;
                font-weight: 850;
                margin-top: 0.2rem;
            }
            .prediction-detail {
                color: #475569;
                font-size: 0.94rem;
                margin-top: 0.25rem;
            }
            .prediction-note {
                color: #374151;
                background: #ffffff;
                border: 1px solid #fecdd3;
                border-radius: 0.55rem;
                font-size: 0.88rem;
                line-height: 1.5;
                margin-top: 0.9rem;
                padding: 0.75rem 0.85rem;
            }
            @media (max-width: 1100px) {
                .listing-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
