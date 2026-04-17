import logging
from typing import Dict, List, Optional

from app.services.normalizer import determine_status, STANDARD_RANGES
from app.models.response_model import CategorySummary, ReportResponse
from app.services.ollama import generate_summary_with_ollama

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category mapping
# ---------------------------------------------------------------------------

CATEGORY_MAP = {
    "blood": "blood",
    "diabetes": "diabetes",
    "cardio": "cardio",
    "urine": "urine",
    "weight": "weight",
    "thyroid": "thyroid",
}

CARDIO_PARAM_NAMES = {
    "Total Cholesterol",
    "LDL",
    "HDL",
    "Triglycerides",
    "VLDL",
    "Chol/HDL Ratio",
    "LDL/HDL Ratio",
}

# Human-readable display names for each category
CATEGORY_DISPLAY = {
    "blood":    "Blood Count",
    "diabetes": "Diabetes",
    "cardio":   "Cardiovascular",
    "urine":    "Urine",
    "weight":   "Weight & BMI",
    "thyroid":  "Thyroid",
}

# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

def _group_parameters(
    parameters: List[Dict[str, object]]
) -> Dict[str, List[Dict[str, object]]]:
    """
    Distribute parameters into their respective category buckets.
    Cardio-named params are always routed to 'cardio' regardless of their
    stored category field.
    """
    grouped: Dict[str, List] = {category: [] for category in CATEGORY_MAP}

    for param in parameters:
        name = param.get("name", "")
        category = (param.get("category") or "").lower().strip()

        if name in CARDIO_PARAM_NAMES or category == "cardio":
            grouped["cardio"].append(param)
        elif category in grouped:
            grouped[category].append(param)
        else:
            # Fallback: unrecognised category goes to blood
            grouped["blood"].append(param)

    return grouped


# ---------------------------------------------------------------------------
# Per-category status helpers
# ---------------------------------------------------------------------------

def _category_status(params: List[Dict[str, object]]) -> str:
    """
    Returns 'normal', 'high', 'low', or 'mixed' for a list of parameters.
    """
    statuses = {p["status"] for p in params if p["status"] in {"high", "low"}}
    if not statuses:
        return "normal"
    if "high" in statuses and "low" in statuses:
        return "mixed"
    return "high" if "high" in statuses else "low"


def _compute_overall_status(parameters: List[Dict[str, object]]) -> str:
    """
    Derives a single overall status from all parameters.
    """
    return _category_status(parameters)


# ---------------------------------------------------------------------------
# Short human-readable category summary (used in the structured response)
# ---------------------------------------------------------------------------

def _build_category_summary(
    params: List[Dict[str, object]], display_name: str
) -> str:
    """
    Returns a single short sentence summarising a category.
    Only called when the category has at least one parameter.
    """
    if not params:
        return ""

    abnormal = [p for p in params if p["status"] != "normal"]

    if not abnormal:
        return f"All {display_name.lower()} values are within the normal range."

    parts = []
    for p in abnormal:
        unit = p.get("unit", "")
        val_str = f"{p['value']} {unit}".strip()
        parts.append(f"{p['name']} is {p['status']} ({val_str})")

    joined = ", ".join(parts)
    return f"{joined}."


# ---------------------------------------------------------------------------
# Key findings list
# ---------------------------------------------------------------------------

def _build_finding(param: Dict[str, object]) -> str:
    unit = param.get("unit", "")
    val_str = f"{param['value']} {unit}".strip()
    return f"{param['name']} is {param['status']} at {val_str}"


def _build_abnormal_summary_line(
    parameters: List[Dict[str, object]]
) -> str:
    """
    Returns a deterministic one-line summary of every abnormal parameter.
    This guarantees abnormal values are mentioned even if the LLM summary
    is brief or selective.
    """
    abnormal = [p for p in parameters if p["status"] in {"high", "low"}]
    if not abnormal:
        return "All extracted values are within the normal range."

    parts = []
    for param in abnormal:
        unit = param.get("unit", "")
        value = f"{param['value']} {unit}".strip()
        parts.append(f"{param['name']} is {param['status']} ({value})")

    return "Abnormal findings: " + ", ".join(parts) + "."


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def _generate_recommendation(
    grouped: Dict[str, List[Dict[str, object]]]
) -> str:
    """
    Builds a recommendation string. Each abnormal category contributes one
    sentence. Returns a single reassuring sentence when all is normal.
    """
    recs: List[str] = []

    abnormal_checks = {
        "blood":    "Review your complete blood count results and repeat the test if your doctor advises.",
        "diabetes": "Follow up on your blood sugar levels and discuss glycemic management with your doctor.",
        "cardio":   "Talk to your doctor about your lipid profile and cardiovascular risk.",
        "urine":    "Discuss your urine test findings with a clinician for further evaluation.",
        "weight":   "Consider lifestyle changes such as a balanced diet and regular exercise to improve body composition.",
        "thyroid":  "Schedule a follow-up with an endocrinologist to review your thyroid function.",
    }

    for category, message in abnormal_checks.items():
        params = grouped.get(category, [])
        if any(p["status"] != "normal" for p in params):
            recs.append(message)

    if not recs:
        return (
            "All your results are within expected ranges. "
            "Keep up your healthy routine and continue with regular check-ups."
        )

    return " ".join(recs)


# ---------------------------------------------------------------------------
# Ollama prompt builder
# ---------------------------------------------------------------------------

def _format_category_for_prompt(
    category_display: str,
    params: List[Dict[str, object]]
) -> str:
    """
    Produces a compact text block for one category, suitable for inclusion
    in the Ollama prompt.
    """
    lines = [f"{category_display}:"]
    for p in params:
        if p["status"] == "normal":
            lines.append(f"  - {p['name']}: normal")
        else:
            unit = p.get("unit", "")
            val_str = f"{p['value']} {unit}".strip()
            lines.append(f"  - {p['name']}: {p['status']} ({val_str})")
    return "\n".join(lines)


def _build_summary_prompt(
    overall_status: str,
    grouped: Dict[str, List[Dict[str, object]]],
    key_findings: List[str],
    recommendation: str,
) -> str:
    """
    Build a detailed prompt for Ollama to generate a conversational doctor summary.
    """
    
    # Identify which categories have abnormal findings with details
    abnormal_details = []
    for cat in CATEGORY_MAP:
        params = grouped.get(cat, [])
        if params and any(p["status"] != "normal" for p in params):
            abnormal = [p["name"] for p in params if p["status"] != "normal"]
            if cat == "blood":
                abnormal_details.append(f"blood count ({', '.join(abnormal)})")
            elif cat == "diabetes":
                abnormal_details.append(f"blood sugar levels ({', '.join(abnormal)})")
            elif cat == "cardio":
                abnormal_details.append(f"cholesterol ({', '.join(abnormal)})")
            elif cat == "thyroid":
                abnormal_details.append(f"thyroid function ({', '.join(abnormal)})")
            elif cat == "urine":
                abnormal_details.append(f"urine test ({', '.join(abnormal)})")
            elif cat == "weight":
                abnormal_details.append(f"weight metrics ({', '.join(abnormal)})")
    
    # Identify which categories are normal
    normal_categories = []
    for cat in CATEGORY_MAP:
        params = grouped.get(cat, [])
        if params and all(p["status"] == "normal" for p in params):
            if cat == "blood":
                normal_categories.append("blood count")
            elif cat == "diabetes":
                normal_categories.append("blood sugar")
            elif cat == "cardio":
                normal_categories.append("cholesterol")
            elif cat == "thyroid":
                normal_categories.append("thyroid")
            elif cat == "urine":
                normal_categories.append("urine")
            elif cat == "weight":
                normal_categories.append("weight")
    
    # Determine tone
    if overall_status == "normal":
        tone_intro = "Great news — all your test results are within the healthy range. "
        tone_closing = "Keep up whatever you're doing, and continue with regular check-ups."
    elif overall_status == "low":
        tone_intro = "Your results are mostly reassuring, but a couple of things need a closer look. "
        tone_closing = "Try to book a follow-up appointment to address these soon."
    elif overall_status == "high":
        tone_intro = "Most of your report looks healthy, but a few areas need attention. "
        tone_closing = "Talk to your doctor about these findings and get a plan in place."
    else:  # mixed
        tone_intro = "A few areas in your report need attention, but overall things look manageable. "
        tone_closing = "Your doctor will help you prioritise what to address first."
    
    abnormal_str = " Your " + ", ".join(abnormal_details) + " need attention." if abnormal_details else ""
    normal_str = " Your " + ", ".join(normal_categories) + " are all looking good." if normal_categories else ""
    
    prompt = (
        f"You are a caring, knowledgeable doctor writing a patient-friendly summary of their lab test results.\n\n"
        f"Overall status: {overall_status}\n"
        f"Abnormal findings: {abnormal_str}\n"
        f"Normal findings: {normal_str}\n"
        f"Recommendations: {recommendation}\n\n"
        f"Write a conversational, warm 4-5 sentence summary that:\n"
        f"1. Opens with: '{tone_intro}'\n"
        f"2. Mentions every abnormal parameter at least once in plain language\n"
        f"3. Provides 1-2 practical, actionable lifestyle tips or next steps\n"
        f"4. Closes with: '{tone_closing}'\n\n"
        f"Keep the tone supportive, honest, and encouraging. Make it feel like a real doctor is talking to the patient.\n\n"
        f"Examples of good summaries:\n"
        f"- 'Great news — all your test results are within the healthy range. Your blood sugar, thyroid, and blood count are all looking good. Keep up whatever you're doing, and continue with your regular annual check-ups.'\n"
        f"- 'Your results are mostly reassuring, but a couple of things need a closer look. Your blood count shows some values running low, and your thyroid is slightly elevated. Focus on eating iron-rich foods and book a follow-up with your doctor soon to discuss these findings.'\n"
        f"- 'Most of your report looks healthy, but your cholesterol is higher than it should be. Try cutting down on oily foods and adding a daily 30-minute walk. Your doctor may want to review this with you as well.'\n\n"
        f"Now write the summary for this patient:"
    )
    
    return prompt


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def build_structured_summary(
    parameters: List[Dict[str, object]],
    raw_text: str,
) -> ReportResponse:
    """
    Accepts a flat list of extracted parameters and returns a fully populated
    ReportResponse, including:
      - per-category summaries (only for categories present in the report)
      - overall status
      - key findings
      - structured recommendation
      - plain-English summary_text generated by Ollama
    """

    # --- Handle empty report gracefully ---
    if not parameters:
        logger.warning("build_structured_summary called with no parameters.")
        return ReportResponse(
            report_type="multi",
            parameters=[],
            overall_status="unknown",
            key_findings=[],
            category_summary=CategorySummary(
                blood="",
                diabetes="",
                cardio="",
                urine="",
                weight="",
                thyroid="",
            ),
            recommendation="No laboratory data could be extracted from this report.",
            summary_text=(
                "We were unable to read any test values from the uploaded report. "
                "Please ensure the PDF is clear and try again, or consult your doctor directly."
            ),
        )

    # --- Group parameters by category ---
    grouped = _group_parameters(parameters)

    # --- Build per-category summaries (empty string when category absent) ---
    category_summary_data = {
        cat: _build_category_summary(grouped[cat], CATEGORY_DISPLAY[cat])
        for cat in CATEGORY_MAP
    }

    # --- Overall status ---
    overall_status = _compute_overall_status(parameters)

    # --- Key findings (only abnormal params) ---
    key_findings: List[str] = [
        _build_finding(p) for p in parameters if p["status"] != "normal"
    ]
    if not key_findings:
        key_findings = ["No abnormal parameters detected."]

    # --- Recommendation ---
    recommendation = _generate_recommendation(grouped)

    # --- Build Ollama prompt and generate summary ---
    prompt_text = _build_summary_prompt(
        overall_status, grouped, key_findings, recommendation
    )

    abnormal_summary_line = _build_abnormal_summary_line(parameters)

    try:
        summary_text = await generate_summary_with_ollama(prompt_text)
        summary_text = summary_text.strip()
    except Exception as exc:
        logger.error("Ollama summary generation failed: %s", exc)
        summary_text = ""

    if summary_text:
        if abnormal_summary_line.startswith("Abnormal findings:"):
            summary_text = f"{abnormal_summary_line}\n\n{summary_text}"
    else:
        summary_text = abnormal_summary_line

    # --- Assemble final response ---
    refined_summary = CategorySummary(
        blood=category_summary_data["blood"],
        diabetes=category_summary_data["diabetes"],
        cardio=category_summary_data["cardio"],
        urine=category_summary_data["urine"],
        weight=category_summary_data["weight"],
        thyroid=category_summary_data["thyroid"],
    )

    serialised_parameters = [
        {
            "name":     p["name"],
            "value":    p["value"],
            "unit":     p.get("unit", ""),
            "category": p.get("category", ""),
            "status":   p["status"],
        }
        for p in parameters
    ]

    # DEBUG: Log all parameters with their status for troubleshooting
    logger.warning("DEBUG PARAMETERS: %s", [
        f"{p['name']}({p.get('value')}) -> {p['status']}" 
        for p in serialised_parameters
    ])

    logger.info(
        "Summary built — overall: %s, categories present: %s, abnormal: %d",
        overall_status,
        [cat for cat in CATEGORY_MAP if grouped[cat]],
        len([p for p in parameters if p["status"] != "normal"]),
    )

    return ReportResponse(
        report_type="multi",
        parameters=serialised_parameters,
        overall_status=overall_status,
        key_findings=key_findings,
        category_summary=refined_summary,
        recommendation=recommendation,
        summary_text=summary_text,
    )
