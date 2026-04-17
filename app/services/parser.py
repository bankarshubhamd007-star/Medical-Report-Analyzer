import re
from typing import Dict, List, Optional

from app.services.normalizer import normalize_parameter
from app.utils.helpers import split_lines

SECTION_PATTERNS = {
    "blood": ["blood", "hematology", "cbc", "complete blood", "hemogram", "red blood cells", "white blood cells"],
    "diabetes": ["diabetes", "blood sugar", "glycemic", "hba1c", "glucose"],
    "cardio": ["cardio", "lipid", "cholesterol", "cardiovascular", "lipids", "triglycerides"],
    "urine": ["urine", "urinalysis", "urine report", "dipstick", "urinal"],
    "weight": ["weight", "bmi", "body fat", "body water", "visceral fat", "metabolic age"],
    "thyroid": ["thyroid", "tsh", "t3", "t4", "free t3", "free t4"],
}

PARAMETER_ALIASES = {
    "hb": ("Hb", "blood"),
    "h b": ("Hb", "blood"),
    "haemoglobin": ("Hb", "blood"),
    "hemoglobin": ("Hb", "blood"),
    "rbc": ("RBC", "blood"),
    "red blood cell": ("RBC", "blood"),
    "red blood cells": ("RBC", "blood"),
    "red cell count": ("RBC", "blood"),
    "wbc": ("WBC", "blood"),
    "white blood cell": ("WBC", "blood"),
    "white blood cells": ("WBC", "blood"),
    "white cell count": ("WBC", "blood"),
    "platelets": ("Platelets", "blood"),
    "hematocrit": ("Hematocrit", "blood"),
    "haematocrit": ("Hematocrit", "blood"),
    "packed cell volume": ("Hematocrit", "blood"),
    "pcv": ("Hematocrit", "blood"),
    "mcv": ("MCV", "blood"),
    "mch": ("MCH", "blood"),
    "mchc": ("MCHC", "blood"),
    "glucose": ("Glucose", "blood"),
    "serum glucose": ("Glucose", "blood"),
    "random glucose": ("Glucose", "blood"),
    "creatinine": ("Creatinine", "blood"),
    "serum creatinine": ("Creatinine", "blood"),
    "urea": ("Urea", "blood"),
    "blood urea": ("Urea", "blood"),
    "sodium": ("Sodium", "blood"),
    "potassium": ("Potassium", "blood"),
    "hba1c": ("HbA1c", "diabetes"),
    "hb a1c": ("HbA1c", "diabetes"),
    "glycated hemoglobin": ("HbA1c", "diabetes"),
    "glycosylated hemoglobin": ("HbA1c", "diabetes"),
    "fasting glucose": ("Fasting Glucose", "diabetes"),
    "fasting blood sugar": ("Fasting Glucose", "diabetes"),
    "postprandial glucose": ("Postprandial Glucose", "diabetes"),
    "post prandial glucose": ("Postprandial Glucose", "diabetes"),
    "postprandial blood sugar": ("Postprandial Glucose", "diabetes"),
    "eag": ("eAG", "diabetes"),
    "insulin": ("Insulin", "diabetes"),
    "c-peptide": ("C-Peptide", "diabetes"),
    "total cholesterol": ("Total Cholesterol", "cardio"),
    "cholesterol": ("Total Cholesterol", "cardio"),
    "ldl": ("LDL", "cardio"),
    "hdl": ("HDL", "cardio"),
    "triglycerides": ("Triglycerides", "cardio"),
    "triglyceride": ("Triglycerides", "cardio"),
    "vldl": ("VLDL", "cardio"),
    "chol/hdl ratio": ("Chol/HDL Ratio", "cardio"),
    "ldl/hdl ratio": ("LDL/HDL Ratio", "cardio"),
    "protein": ("Protein", "urine"),
    "ketones": ("Ketones", "urine"),
    "ph": ("pH", "urine"),
    "specific gravity": ("Specific Gravity", "urine"),
    "epithelial cells": ("Epithelial Cells", "urine"),
    "bacteria": ("Bacteria", "urine"),
    "weight": ("Weight", "weight"),
    "bmi": ("BMI", "weight"),
    "body mass index": ("BMI", "weight"),
    "body fat": ("Body Fat %", "weight"),
    "muscle mass": ("Muscle Mass", "weight"),
    "body water": ("Body Water %", "weight"),
    "bmr": ("BMR", "weight"),
    "visceral fat": ("Visceral Fat", "weight"),
    "bone mass": ("Bone Mass", "weight"),
    "metabolic age": ("Metabolic Age", "weight"),
    "tsh": ("TSH", "thyroid"),
    "t3": ("T3", "thyroid"),
    "t4": ("T4", "thyroid"),
    "free t3": ("Free T3", "thyroid"),
    "free t4": ("Free T4", "thyroid"),
}

NUMBER_PATTERN = r"[-+]?[0-9]*\.?[0-9]+"
UNIT_PATTERN = r"(mg/dl|mmol/l|g/dl|%|kg|lbs|lb|mM|mmol/L|g/L|µIU/mL|ng/mL|ng/dL|µg/dL|kcal|kg/m2|/HPF|score|ratio)?"
RANGE_PATTERN = rf"(?P<min>{NUMBER_PATTERN})\s*(?:-|–|—|to)\s*(?P<max>{NUMBER_PATTERN})\s*(?P<unit>{UNIT_PATTERN})"


def _find_number_and_unit(text: str) -> Optional[Dict[str, str]]:
    match = re.search(rf"({NUMBER_PATTERN})\s*{UNIT_PATTERN}", text, re.IGNORECASE)
    if not match:
        return None
    return {"value": match.group(1), "unit": match.group(2) or ""}


def _find_reference_range(text: str) -> Optional[str]:
    if not text:
        return None

    patterns = [
        rf"\(\s*{RANGE_PATTERN}\s*\)",
        rf"reference(?: range)?\s*[:\-]?\s*{RANGE_PATTERN}",
        rf"ref(?:erence)?\s*[:\-]?\s*{RANGE_PATTERN}",
        RANGE_PATTERN,
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            unit = match.group("unit") or ""
            return f"{match.group('min')}-{match.group('max')} {unit}".strip()
    return None


def _detect_section(line: str) -> Optional[str]:
    normalized = line.lower()
    for section, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(rf"\b{re.escape(pattern)}\b", normalized):
                return section
    return None


def _is_urine_line(text: str) -> bool:
    return any(keyword in text for keyword in ("urine", "urinalysis", "dipstick", "urinal"))


def _match_parameter(line: str, section: Optional[str] = None) -> Optional[Dict[str, str]]:
    normalized = line.lower()
    for alias, (name, category) in sorted(PARAMETER_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(alias)}\b", normalized):
            parsed = _find_number_and_unit(line)
            if not parsed:
                continue

            resolved_category = section or category
            if alias in {"rbc", "wbc", "glucose"} and _is_urine_line(normalized):
                if alias == "glucose":
                    resolved_category = "urine"
                if alias in {"rbc", "wbc"}:
                    resolved_category = "urine"

            reference_range = _find_reference_range(line)
            return {
                "name": name,
                "category": resolved_category,
                "raw_value": parsed["value"],
                "raw_unit": parsed["unit"],
                "reference_range": reference_range,
            }
    return None


def _split_into_sections(text: str) -> Dict[str, List[str]]:
    lines = split_lines(text)
    sections: Dict[str, List[str]] = {key: [] for key in SECTION_PATTERNS}
    current_section: Optional[str] = None
    fallback_lines: List[str] = []

    for line in lines:
        detected = _detect_section(line)
        if detected:
            current_section = detected
            continue
        if current_section:
            sections[current_section].append(line)
        else:
            fallback_lines.append(line)

    if fallback_lines:
        sections.setdefault("fallback", []).extend(fallback_lines)

    return sections


def parse_parameters(text: str) -> List[Dict[str, str]]:
    parameters: Dict[str, Dict[str, object]] = {}
    sections = _split_into_sections(text)

    for section_name, lines in sections.items():
        if section_name == "fallback":
            section_hint = None
        else:
            section_hint = section_name

        for idx, line in enumerate(lines):
            match = _match_parameter(line, section=section_hint)
            if not match:
                continue

            if not match.get("reference_range") and idx + 1 < len(lines):
                next_line = lines[idx + 1]
                if re.search(r"reference|normal range|ref range", next_line, re.IGNORECASE):
                    match["reference_range"] = _find_reference_range(next_line)

            canonical = f"{match['name']}|{match['category']}"
            if canonical in parameters:
                continue

            normalized = normalize_parameter(
                match["name"],
                match["raw_value"],
                match["raw_unit"],
                category=match["category"],
                ref_range=match.get("reference_range"),
            )
            normalized["category"] = match["category"]
            if match.get("reference_range"):
                normalized["reference_range"] = match["reference_range"]
            parameters[canonical] = normalized

    return list(parameters.values())
