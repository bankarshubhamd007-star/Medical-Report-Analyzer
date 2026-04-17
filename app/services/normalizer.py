import re
from typing import Dict, Optional, Tuple

# Blood test parameters
BLOOD_RANGES = {
    "Hb": (12.0, 17.5, "g/dL"),
    "RBC": (4.2, 5.9, "million/µL"),
    "WBC": (4.0, 11.0, "10^3/µL"),
    "Platelets": (150.0, 450.0, "10^3/µL"),
    "Hematocrit": (36.0, 50.0, "%"),
    "MCV": (80.0, 100.0, "fL"),
    "MCH": (27.0, 33.0, "pg"),
    "MCHC": (32.0, 36.0, "g/dL"),
    "Glucose": (70.0, 100.0, "mg/dL"),
    "Creatinine": (0.6, 1.3, "mg/dL"),
    "Urea": (7.0, 20.0, "mg/dL"),
    "Sodium": (135.0, 145.0, "mmol/L"),
    "Potassium": (3.5, 5.1, "mmol/L"),
}

# Diabetes related parameters
DIABETES_RANGES = {
    "HbA1c": (4.0, 5.6, "%"),
    "Fasting Glucose": (70.0, 100.0, "mg/dL"),
    "Postprandial Glucose": (70.0, 140.0, "mg/dL"),
    "eAG": (70.0, 140.0, "mg/dL"),
    "Insulin": (2.0, 25.0, "µIU/mL"),
    "C-Peptide": (0.5, 2.0, "ng/mL"),
}

# Cardiovascular parameters
CARDIO_RANGES = {
    "Total Cholesterol": (125.0, 200.0, "mg/dL"),
    "LDL": (0.0, 100.0, "mg/dL"),
    "HDL": (40.0, 60.0, "mg/dL"),
    "Triglycerides": (0.0, 150.0, "mg/dL"),
    "VLDL": (5.0, 40.0, "mg/dL"),
    "Chol/HDL Ratio": (0.0, 5.0, "ratio"),
    "LDL/HDL Ratio": (0.0, 3.5, "ratio"),
}

# Urine test parameters
URINE_RANGES = {
    "Protein": (0.0, 15.0, "mg/dL"),
    "Ketones": (0.0, 5.0, "mg/dL"),
    "pH": (4.5, 8.0, "pH"),
    "Specific Gravity": (1.005, 1.030, ""),
    "Epithelial Cells": (0.0, 5.0, "/HPF"),
    "Bacteria": (0.0, 1.0, "score"),
}

# Weight and body composition parameters
WEIGHT_RANGES = {
    "Weight": (40.0, 120.0, "kg"),
    "BMI": (18.5, 24.9, "kg/m2"),
    "Body Fat %": (10.0, 24.0, "%"),
    "Muscle Mass": (30.0, 50.0, "%"),
    "Body Water %": (45.0, 60.0, "%"),
    "BMR": (1200.0, 1800.0, "kcal"),
    "Visceral Fat": (1.0, 12.0, "score"),
    "Bone Mass": (2.5, 3.5, "kg"),
    "Metabolic Age": (18.0, 50.0, "years"),
}

# Thyroid parameters
THYROID_RANGES = {
    "TSH": (0.4, 4.0, "µIU/mL"),
    "T3": (0.8, 2.0, "ng/mL"),
    "T4": (4.5, 12.0, "µg/dL"),
    "Free T3": (2.3, 4.2, "pg/mL"),
    "Free T4": (0.8, 1.8, "ng/dL"),
}

# Combined standard ranges for lookup
STANDARD_RANGES = {
    **BLOOD_RANGES,
    **DIABETES_RANGES,
    **CARDIO_RANGES,
    **URINE_RANGES,
    **WEIGHT_RANGES,
    **THYROID_RANGES,
}

CATEGORY_OVERRIDES = {
    "WBC": {
        "blood": (4.0, 11.0, "10^3/µL"),
        "urine": (0.0, 5.0, "/HPF"),
    },
    "RBC": {
        "blood": (4.2, 5.9, "million/µL"),
        "urine": (0.0, 3.0, "/HPF"),
    },
    "Glucose": {
        "blood": (70.0, 100.0, "mg/dL"),
        "urine": (0.0, 130.0, "mg/dL"),
    },
}

UNIT_CLEANUP = {
    "mM": "mmol/L",
    "mmol/L": "mmol/L",
    "mmol/l": "mmol/L",
    "MG/DL": "mg/dL",
    "G/DL": "g/dL",
    "%": "%",
    "KG": "kg",
    "LB": "lb",
    "LBS": "lb",
}


def parse_ref_range(ref_range_str: str) -> Optional[Tuple[float, float]]:
    if not ref_range_str:
        return None
    # Match patterns like "12-15 mg/dL" or "12 to 15"
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)", ref_range_str, re.IGNORECASE)
    if match:
        try:
            low = float(match.group(1))
            high = float(match.group(2))
            return (low, high)
        except ValueError:
            pass
    return None


def normalize_value(raw_value: str) -> Optional[float]:
    try:
        return float(raw_value.replace(",", "."))
    except ValueError:
        return None


def normalize_unit(raw_unit: str) -> str:
    if not raw_unit:
        return ""
    cleaned = raw_unit.strip().lower()
    if cleaned in ("mg/dl", "mgdl"):
        return "mg/dL"
    if cleaned in ("mmol/l", "mmoll"):
        return "mmol/L"
    if cleaned in ("g/dl", "gdl"):
        return "g/dL"
    if cleaned in ("%", "percent"):
        return "%"
    if cleaned in ("kg",):
        return "kg"
    if cleaned in ("lb", "lbs"):
        return "lb"
    if cleaned in ("ph",):
        return "pH"
    return raw_unit


def _get_static_range(name: str, category: Optional[str] = None) -> Optional[Tuple[float, float, str]]:
    if category and name in CATEGORY_OVERRIDES:
        return CATEGORY_OVERRIDES[name].get(category)
    return STANDARD_RANGES.get(name)


def determine_status(name: str, value: Optional[float], ref_range: Optional[str] = None, category: Optional[str] = None) -> str:
    import logging
    logger = logging.getLogger(__name__)
    
    if value is None:
        return "unknown"

    range_tuple = parse_ref_range(ref_range)
    if not range_tuple:
        range_entry = _get_static_range(name, category)
        if not range_entry:
            return "unknown"
        low, high, _ = range_entry
    else:
        low, high = range_tuple

    if value < low:
        status = "low"
    elif value > high:
        status = "high"
    else:
        status = "normal"
        
    # DEBUG
    logger.warning(f"determine_status: {name}={value}, range=[{low},{high}], ref_range={ref_range}, status={status}")
    return status


def normalize_parameter(name: str, raw_value: str, raw_unit: str, category: Optional[str] = None, ref_range: Optional[str] = None) -> Dict[str, object]:
    value = normalize_value(raw_value)
    unit = normalize_unit(raw_unit)
    
    # If no unit from parsing, try to get from static ranges (fallback)
    if not unit:
        range_entry = _get_static_range(name, category)
        if range_entry:
            unit = range_entry[2]

    if value is None:
        value = 0.0

    status = determine_status(name, value, ref_range, category)
    return {
        "name": name,
        "value": round(value, 2),
        "unit": unit or "",
        "status": status,
    }
