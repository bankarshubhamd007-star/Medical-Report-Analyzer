import os
import sys
import requests
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PROJECT_ROOT)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from report_pdf import generate_pdf
from frontend.styled_report import display_styled_report

API_URL   = "http://127.0.0.1:8000/analyze-report"
LOGO_PATH = os.path.join(PROJECT_ROOT, "app", "assets", "logo.png")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="MediScan AI — Medical Report Analyzer",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# UPDATED RESPONSIVE + PREMIUM CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

/* ---- Base ---- */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background-color: #F7F9FB !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    color: #1F2933 !important;
}

/* Center layout for PC */
.block-container {
    max-width: 900px !important;
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
}

#MainMenu, footer, [data-testid="stDecoration"] { display: none !important; }

/* ---- Topbar ---- */
.topbar {
    background: #FFFFFF;
    border: 1px solid #E5EAF0;
    border-radius: 14px;
    padding: 16px 22px;
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

.brand-mark {
    width: 40px;
    height: 40px;
    background: #5ABFA3;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
}

.brand-name {
    font-size: 17px;
    font-weight: 600;
}

.brand-sub {
    font-size: 12px;
    color: #6B7280;
}

/* ---- Hero ---- */
.hero-label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: #5ABFA3;
}

.hero-title {
    font-size: 28px;
    font-weight: 600;
    margin: 6px 0;
}

.hero-desc {
    font-size: 15px;
    color: #6B7280;
    margin-bottom: 1.8rem;
    line-height: 1.6;
}

/* ---- Upload ---- */
[data-testid="stFileUploader"] {
    background: #FFFFFF !important;
    border: 2px dashed #D1D9E0 !important;
    border-radius: 14px !important;
    padding: 1rem !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: #5ABFA3 !important;
}

/* ---- Features ---- */
.feat-strip {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}

.feat-card {
    background: #FFFFFF;
    border: 1px solid #E5EAF0;
    border-radius: 12px;
    padding: 14px;
    transition: 0.2s;
}

.feat-card:hover {
    transform: translateY(-2px);
}

.feat-title {
    font-size: 13px;
    font-weight: 600;
}

.feat-desc {
    font-size: 12px;
    color: #6B7280;
}

/* ---- Button ---- */
.stButton > button {
    background-color: #5ABFA3 !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 10px !important;
    font-size: 15px !important;
}

.stButton > button:hover {
    opacity: 0.9;
}

/* ---- Responsive ---- */
@media (max-width: 768px) {

    .block-container {
        max-width: 100% !important;
        padding: 1rem !important;
    }

    .feat-strip {
        grid-template-columns: 1fr;
    }

    .hero-title {
        font-size: 22px;
    }

    .hero-desc {
        font-size: 14px;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.markdown("""
<div class="topbar">
  <div class="brand-mark">🏥</div>
  <div>
    <div class="brand-name">MediScan AI</div>
    <div class="brand-sub">Medical Report Analyzer</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-label">AI-powered analysis</div>
<div class="hero-title">Upload your medical report</div>
<div class="hero-desc">
  Get a structured, plain-language summary of your lab results in seconds.
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload your report",
    type=["pdf", "png", "jpg", "jpeg"],
)

st.markdown("""
<div class="feat-strip">
  <div class="feat-card">
    <div class="feat-title">🩸 Blood</div>
    <div class="feat-desc">CBC, RBC, WBC</div>
  </div>
  <div class="feat-card">
    <div class="feat-title">🫀 Heart</div>
    <div class="feat-desc">Cholesterol, LDL</div>
  </div>
  <div class="feat-card">
    <div class="feat-title">🔬 Thyroid</div>
    <div class="feat-desc">TSH, HbA1c</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# LOGIC (UNCHANGED)
# ---------------------------------------------------------------------------

if st.button("Analyze Report"):

    if uploaded_file is None:
        st.warning("Upload file first")
    else:
        with st.spinner("Analyzing..."):

            files = {
                "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
            }

            response = requests.post(API_URL, files=files)

            if response.status_code == 200:

                data = response.json()
                st.success("Done!")

                st.markdown("---")

                display_styled_report(data)

                pdf = generate_pdf(data, logo_path=LOGO_PATH)

                st.download_button(
                    "Download PDF",
                    pdf,
                    "report.pdf"
                )

            else:
                st.error("Error from API")
