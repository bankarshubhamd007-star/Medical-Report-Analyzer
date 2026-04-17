from __future__ import annotations

from datetime import datetime
import html
from typing import Dict, Iterable, List

import streamlit as st


THEME = {
    "page_text": "#1F2933",
    "muted_text": "#6B7280",
    "border": "#E5EAF0",
    "border_soft": "#EEF2F6",
    "surface": "#FFFFFF",
    "surface_alt": "#F7FAF9",
    "accent": "#5ABFA3",
    "ok": "#2F855A",
    "ok_bg": "#EAF7F2",
    "warn": "#C0841A",
    "warn_bg": "#FFF6E5",
    "bad": "#D64545",
    "bad_bg": "#FDECEC",
}

CATEGORY_ORDER = ["blood", "diabetes", "cardio", "thyroid", "urine", "weight"]
CATEGORY_LABELS = {
    "blood": "Blood Count",
    "diabetes": "Diabetes",
    "cardio": "Cardiovascular",
    "thyroid": "Thyroid",
    "urine": "Urine",
    "weight": "Weight & BMI",
}


def _inject_styles() -> None:
    st.markdown(
        f"""
<style>
.report-shell {{
    color: {THEME["page_text"]};
}}

.report-title {{
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 0.25rem;
}}

.report-subtitle {{
    font-size: 13px;
    color: {THEME["muted_text"]};
    margin-bottom: 0.9rem;
}}

.report-badge {{
    display: inline-block;
    padding: 0.35rem 0.8rem;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}}

.section-label {{
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: {THEME["muted_text"]};
    border-bottom: 1px solid {THEME["border_soft"]};
    padding-bottom: 0.45rem;
    margin: 1.35rem 0 0.8rem;
}}

.summary-card {{
    background: {THEME["surface_alt"]};
    border: 1px solid {THEME["border"]};
    border-left: 4px solid {THEME["accent"]};
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.6rem;
    line-height: 1.7;
}}

.category-card {{
    background: {THEME["surface"]};
    border: 1px solid {THEME["border"]};
    border-radius: 14px;
    padding: 0.95rem 1rem 0.7rem;
    margin-bottom: 0.9rem;
}}

.category-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 0.8rem;
}}

.category-title {{
    font-size: 14px;
    font-weight: 600;
    color: {THEME["page_text"]};
}}

.category-pill {{
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
}}

.row-head {{
    font-size: 11px;
    font-weight: 600;
    color: {THEME["muted_text"]};
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.35rem;
}}

.param-divider {{
    border-top: 1px solid {THEME["border_soft"]};
    margin: 0.55rem 0;
}}

.param-name {{
    font-size: 13px;
    font-weight: 600;
    color: {THEME["page_text"]};
}}

.param-meta {{
    font-size: 12px;
    color: {THEME["muted_text"]};
}}

.status-chip {{
    display: inline-block;
    padding: 0.22rem 0.55rem;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
}}

.recommend-card {{
    background: {THEME["surface"]};
    border: 1px solid {THEME["border"]};
    border-radius: 14px;
    padding: 0.9rem 1rem;
}}

.recommend-item {{
    color: {THEME["page_text"]};
    font-size: 13px;
    line-height: 1.65;
    margin: 0.35rem 0;
}}

.report-footnote {{
    margin-top: 1rem;
    font-size: 12px;
    color: {THEME["muted_text"]};
}}
</style>
""",
        unsafe_allow_html=True,
    )


def _escape(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _group_parameters(parameters: Iterable[dict]) -> Dict[str, List[dict]]:
    grouped: Dict[str, List[dict]] = {key: [] for key in CATEGORY_ORDER}
    for parameter in parameters:
        category = str(parameter.get("category") or "blood").lower().strip()
        grouped.get(category, grouped["blood"]).append(parameter)
    return grouped


def _status_theme(status: str) -> tuple[str, str, str]:
    normalized = (status or "unknown").lower()
    if normalized == "high":
        return THEME["bad"], THEME["bad_bg"], "High"
    if normalized == "low":
        return THEME["warn"], THEME["warn_bg"], "Low"
    if normalized == "normal":
        return THEME["ok"], THEME["ok_bg"], "Normal"
    return THEME["muted_text"], "#F3F4F6", normalized.capitalize() or "Unknown"


def _overall_badge(overall_status: str) -> tuple[str, str, str]:
    normalized = (overall_status or "unknown").lower()
    if normalized == "high":
        return THEME["bad_bg"], THEME["bad"], "Needs review"
    if normalized == "low":
        return THEME["warn_bg"], THEME["warn"], "Monitor values"
    if normalized == "normal":
        return THEME["ok_bg"], THEME["ok"], "Within range"
    return "#F3F4F6", THEME["muted_text"], "Report analyzed"


def _category_pill(params: List[dict]) -> tuple[str, str, str]:
    statuses = {(param.get("status") or "unknown").lower() for param in params}
    if not statuses or statuses <= {"normal"}:
        return THEME["ok_bg"], THEME["ok"], "All normal"
    if "high" in statuses:
        return THEME["bad_bg"], THEME["bad"], "Review needed"
    if "low" in statuses:
        return THEME["warn_bg"], THEME["warn"], "Monitor"
    return "#F3F4F6", THEME["muted_text"], "Check"


def _format_measurement(parameter: dict) -> str:
    value = parameter.get("value")
    unit = str(parameter.get("unit") or "").strip()
    if value in (None, ""):
        return "—"
    return f"{value} {unit}".strip()


def _format_reference(parameter: dict) -> str:
    reference = parameter.get("reference_range") or parameter.get("ref_range") or ""
    reference = str(reference).strip()
    return reference or "—"


def _parse_recommendations(text: str) -> List[str]:
    if not text:
        return []
    return [item.strip() for item in str(text).split(".") if item.strip()]


def _render_header(patient_name: str, overall_status: str) -> None:
    badge_bg, badge_fg, badge_text = _overall_badge(overall_status)
    today = datetime.now().strftime("%d %b %Y")
    st.markdown(
        f"""
<div class="report-shell">
  <div class="report-title">Lab Report Summary</div>
  <div class="report-subtitle">
    Patient: {_escape(patient_name)} | Report date: {_escape(today)} | Generated by MediScan AI
  </div>
  <span class="report-badge" style="background:{badge_bg}; color:{badge_fg};">{_escape(badge_text)}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_summary(summary_text: str) -> None:
    if not summary_text:
        return
    paragraphs = [part.strip() for part in str(summary_text).split("\n\n") if part.strip()]
    summary_html = "<br><br>".join(_escape(paragraph) for paragraph in paragraphs)
    st.markdown('<div class="section-label">Summary</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="summary-card">{summary_html}</div>',
        unsafe_allow_html=True,
    )


def _render_param_table(parameters: List[dict]) -> None:
    header_cols = st.columns([2.2, 1.4, 1.5, 1.1])
    headers = ["Parameter", "Value", "Reference", "Status"]
    for col, header in zip(header_cols, headers):
        col.markdown(f'<div class="row-head">{header}</div>', unsafe_allow_html=True)

    for index, parameter in enumerate(parameters):
        cols = st.columns([2.2, 1.4, 1.5, 1.1])
        status_color, status_bg, status_label = _status_theme(str(parameter.get("status", "")))
        cols[0].markdown(
            f"""
<div class="param-name">{_escape(parameter.get("name") or "Unknown")}</div>
<div class="param-meta">{_escape(str(parameter.get("category") or "").title())}</div>
""",
            unsafe_allow_html=True,
        )
        cols[1].write(_format_measurement(parameter))
        cols[2].write(_format_reference(parameter))
        cols[3].markdown(
            f'<span class="status-chip" style="background:{status_bg}; color:{status_color};">{_escape(status_label)}</span>',
            unsafe_allow_html=True,
        )
        if index < len(parameters) - 1:
            st.markdown('<div class="param-divider"></div>', unsafe_allow_html=True)


def _render_category_card(category_key: str, parameters: List[dict]) -> None:
    pill_bg, pill_fg, pill_label = _category_pill(parameters)
    
    # Filter to show only abnormal parameters (low or high)
    abnormal_params = [p for p in parameters if (p.get("status") or "").lower() not in ("normal", "")]
    
    with st.container(border=True):
        st.markdown(
            f"""
<div class="category-header">
  <div class="category-title">{_escape(CATEGORY_LABELS.get(category_key, category_key.title()))}</div>
  <span class="category-pill" style="background:{pill_bg}; color:{pill_fg};">{_escape(pill_label)}</span>
</div>
""",
            unsafe_allow_html=True,
        )
        
        # Show only abnormal parameters, or a message if all are normal
        if abnormal_params:
            _render_param_table(abnormal_params)
        else:
            st.markdown(
                '<div style="color: #6B7280; font-size: 13px; font-style: italic;">All values within normal range</div>',
                unsafe_allow_html=True,
            )


def _render_results(grouped: Dict[str, List[dict]]) -> None:
    active_categories = [key for key in CATEGORY_ORDER if grouped.get(key)]
    if not active_categories:
        return

    st.markdown('<div class="section-label">Results By Category</div>', unsafe_allow_html=True)
    for start in range(0, len(active_categories), 2):
        left_col, right_col = st.columns(2)
        pair = active_categories[start : start + 2]
        for col, category_key in zip((left_col, right_col), pair):
            with col:
                _render_category_card(category_key, grouped[category_key])


def _render_recommendations(text: str) -> None:
    items = _parse_recommendations(text)
    if not items:
        return
    st.markdown('<div class="section-label">Recommendations</div>', unsafe_allow_html=True)
    with st.container(border=True):
        for item in items:
            st.markdown(f'<div class="recommend-item">• {_escape(item)}</div>', unsafe_allow_html=True)


def _render_footer() -> None:
    st.markdown(
        '<div class="report-footnote">AI-generated interpretation for informational use only. Always confirm with a qualified clinician.</div>',
        unsafe_allow_html=True,
    )


def render_styled_report(data: dict, patient_name: str = "Patient") -> dict:
    parameters = data.get("parameters") or []
    return {
        "patient_name": patient_name,
        "summary_text": (data.get("summary_text") or "").strip(),
        "overall_status": data.get("overall_status", "unknown"),
        "grouped_parameters": _group_parameters(parameters),
        "recommendation": data.get("recommendation", ""),
    }


def display_styled_report(data: dict, patient_name: str = "Patient") -> None:
    view_model = render_styled_report(data, patient_name)
    _inject_styles()
    _render_header(view_model["patient_name"], view_model["overall_status"])
    _render_summary(view_model["summary_text"])
    _render_results(view_model["grouped_parameters"])
    _render_recommendations(view_model["recommendation"])
    _render_footer()
