import streamlit as st

# ---------------------------------------------------------------------------
# LIGHT THEME (MATCHES MAIN APP)
# ---------------------------------------------------------------------------

LIGHT = {
    "card_bg": "#FFFFFF",
    "card_border": "#E5EAF0",
    "divider": "#EEF2F6",

    "text_main": "#1F2933",
    "text_muted": "#4B5563",
    "text_hint": "#6B7280",
    "label_color": "#6B7280",

    "summary_bg": "#F7FAF9",
    "summary_border": "#E5EAF0",
    "summary_accent": "#5ABFA3",

    "badge_ok_bg": "#EAF7F2",
    "badge_ok_text": "#2F855A",

    "badge_warn_bg": "#FFF6E5",
    "badge_warn_text": "#B7791F",

    "badge_err_bg": "#FDECEC",
    "badge_err_text": "#C53030",

    "no_summary_bg": "#F8FAFC",
    "no_summary_text": "#4B5563",
    "no_summary_bdr": "#E5EAF0",
}

def _get_theme():
    return LIGHT

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _count_abnormal(parameters):
    return sum(1 for p in parameters if p.get("status", "normal") != "normal")

def _overall_pill(status, t):
    if status == "normal":
        return t["badge_ok_bg"], t["badge_ok_text"], "All normal"
    elif status == "high":
        return t["badge_err_bg"], t["badge_err_text"], "Some elevated"
    elif status == "low":
        return t["badge_warn_bg"], t["badge_warn_text"], "Some low"
    return t["badge_warn_bg"], t["badge_warn_text"], "Needs attention"

# ---------------------------------------------------------------------------
# SUMMARY UI
# ---------------------------------------------------------------------------

def _build_summary_html(summary, status, total, abnormal, t):

    bg, color, label = _overall_pill(status, t)
    normal = total - abnormal

    return f"""
<style>
.esw {{
    max-width: 900px;
    margin: auto;
    padding: 1rem;
    font-family: "Inter", sans-serif;
}}

.section-label {{
    font-size: 12px;
    font-weight: 600;
    color: {t["label_color"]};
    border-bottom: 1px solid {t["divider"]};
    padding-bottom: 6px;
    margin-bottom: 12px;
    text-transform: uppercase;
}}

.stat-row {{
    margin-bottom: 16px;
}}

.stat-chip {{
    display: inline-block;
    padding: 7px 16px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 500;
}}

.summary-card {{
    background: {t["summary_bg"]};
    border: 1px solid {t["summary_border"]};
    border-left: 4px solid {t["summary_accent"]};
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}}

.summary-card p {{
    font-size: 15px;
    line-height: 1.8;
    color: {t["text_main"]};
}}

.meta-row {{
    display: flex;
    gap: 18px;
    margin-top: 12px;
    flex-wrap: wrap;
}}

.meta-item {{
    font-size: 13px;
    color: {t["text_hint"]};
}}

.meta-val {{
    font-weight: 600;
    color: {t["text_muted"]};
}}

/* MOBILE */
@media (max-width: 768px) {{
    .esw {{
        padding: 0.8rem;
    }}

    .summary-card {{
        padding: 14px;
    }}

    .summary-card p {{
        font-size: 14px;
    }}
}}
</style>

<div class="esw">

    <div class="section-label">Easy summary</div>

    <div class="stat-row">
        <span class="stat-chip" style="background:{bg}; color:{color};">
            {label}
        </span>
    </div>

    <div class="summary-card">
        <p>{summary}</p>

        <div class="meta-row">
            <div class="meta-item">
                Tests: <span class="meta-val">{total}</span>
            </div>

            <div class="meta-item">
                Normal: <span class="meta-val" style="color:{t['badge_ok_text']}">{normal}</span>
            </div>

            {"" if abnormal == 0 else f'''
            <div class="meta-item">
                Attention: <span class="meta-val" style="color:{t['badge_err_text']}">{abnormal}</span>
            </div>
            '''}
        </div>
    </div>

</div>
"""

# ---------------------------------------------------------------------------
# NO SUMMARY UI
# ---------------------------------------------------------------------------

def _build_no_summary_html(total, t):

    return f"""
<style>
.esw-ns {{
    max-width: 900px;
    margin: auto;
    padding: 1rem;
    font-family: "Inter", sans-serif;
}}

.section-label {{
    font-size: 12px;
    font-weight: 600;
    color: {t["label_color"]};
    border-bottom: 1px solid {t["divider"]};
    padding-bottom: 6px;
    margin-bottom: 12px;
}}

.notice-card {{
    background: {t["no_summary_bg"]};
    border: 1px solid {t["no_summary_bdr"]};
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}}

.notice-title {{
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 6px;
    color: {t["text_main"]};
}}

.notice-desc {{
    font-size: 13px;
    color: {t["text_muted"]};
    line-height: 1.6;
}}
</style>

<div class="esw-ns">

    <div class="section-label">Easy summary</div>

    <div class="notice-card">
        <div class="notice-title">Summary unavailable</div>
        <div class="notice-desc">
            {total} test values extracted. Please review the detailed report below.
        </div>
    </div>

</div>
"""

# ---------------------------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------------------------

def display_short_summary(data: dict) -> bool:

    t = _get_theme()

    summary = (data.get("summary_text") or "").strip()
    params = data.get("parameters") or []
    status = data.get("overall_status", "normal")

    if not params:
        st.warning("No report data found.")
        return False

    total = len(params)
    abnormal = _count_abnormal(params)

    if summary:
        st.markdown(
            _build_summary_html(summary, status, total, abnormal, t),
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            _build_no_summary_html(total, t),
            unsafe_allow_html=True
        )

    return True