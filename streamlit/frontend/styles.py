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
            [data-testid="stTabs"] {
                margin-top: 0.15rem;
            }
            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                border-bottom: 1px solid #e5e7eb;
                gap: 0.5rem;
            }
            [data-testid="stTabs"] [data-baseweb="tab"] {
                background: #ffffff !important;
                border: 1px solid transparent !important;
                border-radius: 0.5rem 0.5rem 0 0 !important;
                color: #334155 !important;
                font-weight: 850 !important;
                opacity: 1 !important;
                padding: 0.7rem 0.9rem !important;
            }
            [data-testid="stTabs"] [data-baseweb="tab"] p,
            [data-testid="stTabs"] [data-baseweb="tab"] span {
                color: #334155 !important;
                font-size: 0.92rem !important;
                font-weight: 850 !important;
                opacity: 1 !important;
            }
            [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
                background: #fff1f2 !important;
                border-color: #fecdd3 !important;
                border-bottom-color: #ffffff !important;
                color: #be123c !important;
            }
            [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] p,
            [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] span {
                color: #be123c !important;
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
            .dvf-map-loading-overlay {
                animation: dvf-loader-hide 0.25s ease 2.8s forwards;
                height: 0;
                opacity: 1;
                pointer-events: none;
                position: relative;
                visibility: visible;
                z-index: 20;
            }
            .dvf-map-loading-panel {
                align-items: center;
                background: #ffffff;
                color: #111827;
                display: flex;
                height: 720px;
                justify-content: center;
                left: 0;
                position: absolute;
                text-align: center;
                top: 0;
                width: 100%;
            }
            .dvf-map-loader {
                animation: dvf-loader-spin 0.8s linear infinite;
                border: 4px solid #fee2e2;
                border-radius: 999px;
                border-top-color: #e11d48;
                height: 38px;
                margin: 0 auto 0.75rem;
                width: 38px;
            }
            .dvf-map-loading-title {
                font-size: 0.95rem;
                font-weight: 800;
            }
            .dvf-map-loading-subtitle {
                color: #64748b;
                font-size: 0.82rem;
                margin-top: 0.2rem;
            }
            @keyframes dvf-loader-spin {
                to {
                    transform: rotate(360deg);
                }
            }
            @keyframes dvf-loader-hide {
                to {
                    opacity: 0;
                    visibility: hidden;
                }
            }
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
            .map-welcome h2 {
                color: #111827;
                font-size: 1.85rem;
                font-weight: 850;
                letter-spacing: 0;
                line-height: 1.25;
                margin: 0 0 0.65rem;
            }
            .map-welcome p {
                color: #374151;
                font-size: 1rem;
                line-height: 1.65;
                margin: 0 0 1rem;
                max-width: 520px;
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
            .prediction-history-card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-top: 3px solid #fb7185;
                border-radius: 0.75rem;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
                margin: 0 0 0.65rem;
                padding: 1rem;
            }
            .prediction-history-card-top {
                align-items: center;
                display: flex;
                gap: 0.75rem;
                justify-content: space-between;
            }
            .prediction-history-source {
                background: #fff1f2;
                border: 1px solid #fecdd3;
                border-radius: 999px;
                color: #be123c;
                display: inline-flex;
                font-size: 0.72rem;
                font-weight: 850;
                letter-spacing: 0.035em;
                padding: 0.25rem 0.55rem;
                text-transform: uppercase;
            }
            .prediction-history-date {
                color: #94a3b8;
                font-size: 0.76rem;
                font-weight: 750;
            }
            .prediction-history-price {
                color: #111827;
                font-size: 1.55rem;
                font-weight: 850;
                margin-top: 0.85rem;
            }
            .prediction-history-location {
                color: #475569;
                font-size: 0.88rem;
                font-weight: 750;
                margin-top: 0.18rem;
            }
            .prediction-history-details {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.55rem;
                border-top: 1px solid #eef2f7;
                color: #64748b;
                font-size: 0.78rem;
                margin-top: 0.85rem;
                padding-top: 0.75rem;
            }
            .prediction-history-details span:last-child {
                grid-column: 1 / -1;
            }
            .prediction-history-details strong {
                color: #111827;
                display: block;
                font-size: 0.88rem;
                font-weight: 850;
            }
            [class*="st-key-effacer_prediction_"] {
                margin: -0.2rem 0 0.95rem;
            }
            [class*="st-key-effacer_prediction_"] button {
                background: #ffffff !important;
                border: 1px solid #fb7185 !important;
                border-radius: 0.55rem !important;
                color: #be123c !important;
                font-weight: 850 !important;
                min-height: 42px !important;
            }
            [class*="st-key-effacer_prediction_"] button:hover {
                background: #fff1f2 !important;
                border-color: #e11d48 !important;
                color: #be123c !important;
            }
            [class*="st-key-effacer_prediction_"] button p,
            [class*="st-key-effacer_prediction_"] button span {
                color: #be123c !important;
                opacity: 1 !important;
            }
            .address-history-card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-top: 3px solid #fb7185;
                border-radius: 0.75rem;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
                margin: 0 0 0.65rem;
                padding: 1rem;
            }
            .address-history-card-top {
                align-items: center;
                display: flex;
                gap: 0.75rem;
                justify-content: space-between;
            }
            .address-history-source {
                background: #fff1f2;
                border: 1px solid #fecdd3;
                border-radius: 999px;
                color: #be123c;
                display: inline-flex;
                font-size: 0.72rem;
                font-weight: 850;
                letter-spacing: 0.035em;
                padding: 0.25rem 0.55rem;
                text-transform: uppercase;
            }
            .address-history-date {
                color: #94a3b8;
                font-size: 0.76rem;
                font-weight: 750;
            }
            .address-history-title {
                color: #111827;
                font-size: 1.2rem;
                font-weight: 850;
                margin-top: 0.85rem;
                word-break: break-word;
            }
            .address-history-location {
                color: #475569;
                font-size: 0.88rem;
                font-weight: 750;
                margin-top: 0.18rem;
            }
            .address-history-details {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.55rem;
                border-top: 1px solid #eef2f7;
                color: #64748b;
                font-size: 0.78rem;
                margin-top: 0.85rem;
                padding-top: 0.75rem;
            }
            .address-history-details strong {
                color: #111827;
                display: block;
                font-size: 0.88rem;
                font-weight: 850;
            }
            [class*="st-key-effacer_adresse_"] {
                margin: -0.2rem 0 0.95rem;
            }
            [class*="st-key-effacer_adresse_"] button {
                background: #ffffff !important;
                border: 1px solid #fb7185 !important;
                border-radius: 0.55rem !important;
                color: #be123c !important;
                font-weight: 850 !important;
                min-height: 42px !important;
            }
            [class*="st-key-effacer_adresse_"] button:hover {
                background: #fff1f2 !important;
                border-color: #e11d48 !important;
                color: #be123c !important;
            }
            [class*="st-key-effacer_adresse_"] button p,
            [class*="st-key-effacer_adresse_"] button span {
                color: #be123c !important;
                opacity: 1 !important;
            }
            .auth-shell {
                background:
                    radial-gradient(circle at top left, rgba(251, 113, 133, 0.18), transparent 32%),
                    linear-gradient(135deg, #fff7f8 0%, #ffffff 58%, #f8fafc 100%);
                border: 1px solid #ffe4e6;
                border-radius: 1.1rem;
                box-shadow: 0 20px 50px rgba(15, 23, 42, 0.06);
                margin: 0 auto 1.2rem;
                max-width: 860px;
                padding: 2.2rem 2.4rem;
                text-align: center;
            }
            .auth-badge {
                background: #fff1f2;
                border: 1px solid #fecdd3;
                border-radius: 999px;
                color: #be123c;
                display: inline-flex;
                font-size: 0.82rem;
                font-weight: 850;
                letter-spacing: 0;
                margin-bottom: 0.85rem;
                padding: 0.35rem 0.8rem;
            }
            .auth-shell h1 {
                color: #111827;
                font-size: 2.35rem;
                font-weight: 850;
                letter-spacing: 0;
                line-height: 1.15;
                margin: 0;
            }
            .auth-shell p {
                color: #475569;
                font-size: 1.04rem;
                line-height: 1.6;
                margin: 0.9rem auto 0;
                max-width: 620px;
            }
            [data-testid="stPopover"] button {
                background: #fff1f2 !important;
                border: 1px solid #fb7185 !important;
                border-radius: 0.75rem !important;
                color: #be123c !important;
                font-weight: 850 !important;
                min-height: 64px;
            }
            [data-testid="stPopover"] button p,
            [data-testid="stPopover"] button span {
                color: #be123c !important;
                font-weight: 850 !important;
                opacity: 1 !important;
            }
            .account-email {
                background: rgba(148, 163, 184, 0.12);
                border: 1px solid rgba(148, 163, 184, 0.24);
                border-radius: 999px;
                color: #cbd5e1;
                display: inline-flex;
                font-size: 0.86rem;
                font-weight: 750;
                line-height: 1.2;
                margin-top: 0.45rem;
                padding: 0.35rem 0.65rem;
                text-decoration: none;
                word-break: break-word;
            }
            .admin-user-card,
            .admin-history-card {
                align-items: center;
                background:
                    radial-gradient(circle at top right, rgba(251, 113, 133, 0.10), transparent 35%),
                    #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 0.9rem;
                box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
                display: flex;
                gap: 1rem;
                justify-content: space-between;
                margin: 0.85rem 0 0.75rem;
                padding: 1rem 1.05rem;
            }
            .admin-card-kicker {
                color: #e11d48;
                font-size: 0.74rem;
                font-weight: 900;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }
            .admin-card-title {
                color: #111827;
                font-size: 1.08rem;
                font-weight: 900;
                margin-top: 0.2rem;
                word-break: break-word;
            }
            .admin-card-subtitle {
                color: #64748b;
                font-size: 0.9rem;
                font-weight: 650;
                margin-top: 0.2rem;
            }
            .admin-badge-row,
            .admin-chip-row {
                align-items: center;
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem;
            }
            .admin-badge,
            .admin-chip {
                border-radius: 999px;
                display: inline-flex;
                font-size: 0.76rem;
                font-weight: 850;
                line-height: 1;
                padding: 0.45rem 0.65rem;
            }
            .admin-badge-admin {
                background: #fff1f2;
                border: 1px solid #fecdd3;
                color: #be123c;
            }
            .admin-badge-super {
                background: #111827;
                border: 1px solid #111827;
                color: #ffffff;
            }
            .admin-badge-user {
                background: #ecfdf5;
                border: 1px solid #bbf7d0;
                color: #047857;
            }
            .admin-badge-active {
                background: #eef2ff;
                border: 1px solid #c7d2fe;
                color: #4338ca;
            }
            .admin-badge-muted {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                color: #64748b;
            }
            .admin-info-grid {
                display: grid;
                gap: 0.65rem;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                margin: 0.2rem 0 0.9rem;
            }
            .admin-info-grid div {
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 0.7rem;
                padding: 0.7rem 0.8rem;
            }
            .admin-info-grid span,
            .admin-history-side span {
                color: #64748b;
                display: block;
                font-size: 0.78rem;
                font-weight: 750;
                margin-bottom: 0.2rem;
            }
            .admin-info-grid strong,
            .admin-history-side strong {
                color: #111827;
                display: block;
                font-size: 0.94rem;
                font-weight: 900;
                word-break: break-word;
            }
            .admin-history-card {
                border-left: 4px solid #fb7185;
                margin-bottom: 0.9rem;
                padding: 1.1rem 1.15rem;
            }
            .admin-history-title {
                color: #111827;
                font-size: 1.65rem;
                font-weight: 950;
                letter-spacing: -0.03em;
                margin: 0.25rem 0 0.7rem;
            }
            .admin-address-title {
                color: #111827;
                font-size: 1.08rem;
                font-weight: 900;
                margin: 0.25rem 0 0.7rem;
                word-break: break-word;
            }
            .admin-chip {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                color: #475569;
            }
            .admin-history-side {
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 0.8rem;
                min-width: 230px;
                padding: 0.85rem 0.95rem;
                text-align: right;
            }
            [class*="st-key-admin_save_role_"] button {
                background: #fff1f2 !important;
                border: 1px solid #fb7185 !important;
                border-radius: 0.55rem !important;
                color: #be123c !important;
                font-weight: 850 !important;
                min-height: 42px !important;
            }
            [class*="st-key-admin_save_role_"] button:hover {
                background: #ffe4e6 !important;
                border-color: #e11d48 !important;
            }
            [class*="st-key-admin_delete_user_"] button {
                background: #ffffff !important;
                border: 1px solid #fecaca !important;
                border-radius: 0.55rem !important;
                color: #b91c1c !important;
                font-weight: 850 !important;
                min-height: 42px !important;
            }
            [class*="st-key-admin_delete_user_"] button:hover {
                background: #fef2f2 !important;
                border-color: #ef4444 !important;
            }
            [class*="st-key-admin_save_role_"] button p,
            [class*="st-key-admin_save_role_"] button span {
                color: #be123c !important;
                opacity: 1 !important;
            }
            [class*="st-key-admin_delete_user_"] button p,
            [class*="st-key-admin_delete_user_"] button span {
                color: #b91c1c !important;
                opacity: 1 !important;
            }
            [class*="st-key-admin_save_role_"] button:disabled,
            [class*="st-key-admin_delete_user_"] button:disabled {
                background: #f8fafc !important;
                border-color: #e2e8f0 !important;
            }
            [class*="st-key-admin_save_role_"] button:disabled p,
            [class*="st-key-admin_save_role_"] button:disabled span,
            [class*="st-key-admin_delete_user_"] button:disabled p,
            [class*="st-key-admin_delete_user_"] button:disabled span {
                color: #94a3b8 !important;
            }
            @media (max-width: 1100px) {
                .auth-shell {
                    padding: 1.65rem 1.25rem;
                }
                .auth-shell h1 {
                    font-size: 1.75rem;
                }
                .auth-shell p {
                    font-size: 0.96rem;
                }
                .listing-grid {
                    grid-template-columns: 1fr;
                }
                .admin-user-card,
                .admin-history-card {
                    align-items: flex-start;
                    flex-direction: column;
                }
                .admin-history-side {
                    min-width: 0;
                    text-align: left;
                    width: 100%;
                }
                .admin-info-grid {
                    grid-template-columns: 1fr;
                }
            }
            @media (max-width: 700px) {
                [data-testid="stButtonGroup"] [data-baseweb="button-group"] {
                    display: grid;
                    gap: 0.55rem;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
                [data-testid="stButtonGroup"] button {
                    min-height: 58px;
                    padding: 0.65rem 0.5rem !important;
                    width: 100%;
                }
                [data-testid="stButtonGroup"] button p {
                    font-size: 0.9rem !important;
                    hyphens: none !important;
                    line-height: 1.15 !important;
                    overflow-wrap: normal !important;
                    word-break: normal !important;
                }
                .prediction-history-card {
                    padding: 0.95rem;
                }
                .prediction-history-price {
                    font-size: 1.42rem;
                }
                .address-history-card {
                    padding: 0.95rem;
                }
                .address-history-title {
                    font-size: 1.06rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
