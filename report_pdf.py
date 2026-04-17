import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable


NAVY        = colors.HexColor("#0D2B4E")
TEAL        = colors.HexColor("#1A6B72")
LIGHT_TEAL  = colors.HexColor("#E8F4F5")
MID_BLUE    = colors.HexColor("#2A5F8F")
STEEL       = colors.HexColor("#5A7A9A")
WHITE       = colors.white
LIGHT_GREY  = colors.HexColor("#F4F6F9")
BORDER_GREY = colors.HexColor("#CBD5E0")
RED_ALERT   = colors.HexColor("#C0392B")
AMBER       = colors.HexColor("#E67E22")
GREEN_OK    = colors.HexColor("#1E8449")
DARK_TEXT   = colors.HexColor("#1A202C")
GOLD        = colors.HexColor("#C9A84C")

CATEGORY_ORDER = ["blood", "diabetes", "cardio", "thyroid", "urine", "weight", "general"]
CATEGORY_LABELS = {
    "blood":    "Blood Test",
    "diabetes": "Diabetes Test",
    "cardio":   "Heart Health",
    "thyroid":  "Thyroid Test",
    "urine":    "Urine Test",
    "weight":   "Weight & Body Metrics",
    "general":  "General Health",
}


class HeaderBanner(Flowable):
    def __init__(self, logo_path, width, report_date):
        Flowable.__init__(self)
        self.logo_path = logo_path
        self.bw = width
        self.bh = 1.45 * inch
        self.report_date = report_date

    def draw(self):
        c = self.canv
        w, h = self.bw, self.bh

        c.setFillColor(NAVY)
        c.rect(0, 0, w, h, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#122E52"))
        c.rect(0, h * 0.55, w, h * 0.45, fill=1, stroke=0)

        c.setFillColor(GOLD)
        c.rect(0, 0, w, 3, fill=1, stroke=0)

        c.setFillColor(TEAL)
        c.rect(0, 3, 8, h - 3, fill=1, stroke=0)

        LOGO_CX = 18 + 8 + 0.52 * inch
        LOGO_CY = h / 2
        LOGO_R = 0.48 * inch

        c.setFillColor(colors.HexColor("#1F4070"))
        c.circle(LOGO_CX, LOGO_CY, LOGO_R + 4, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#0D2B4E"))
        c.circle(LOGO_CX, LOGO_CY, LOGO_R, fill=1, stroke=0)

        LOGO_W = LOGO_H = 2 * LOGO_R * 0.82
        LOGO_X = LOGO_CX - LOGO_W / 2
        LOGO_Y = LOGO_CY - LOGO_H / 2

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                c.drawImage(self.logo_path, LOGO_X, LOGO_Y,
                            width=LOGO_W, height=LOGO_H,
                            preserveAspectRatio=True, mask="auto")
            except Exception:
                pass
        else:
            c.setFillColor(TEAL)
            c.circle(LOGO_CX, LOGO_CY, LOGO_R * 0.78, fill=1, stroke=0)
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(LOGO_CX, LOGO_CY - 7, "M+")

        TEXT_X = LOGO_CX + LOGO_R + 16
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(TEXT_X, h * 0.60, "Dr. Store by Tracky")

        c.setFillColor(GOLD)
        c.setFont("Helvetica", 8)
        c.drawString(TEXT_X, h * 0.42, "Precision Health Intelligence Platform")

        c.setStrokeColor(GOLD)
        c.setLineWidth(0.5)
        c.line(TEXT_X, h * 0.37, TEXT_X + 220, h * 0.37)

        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(w - 16, h * 0.63, "MEDICAL REPORT ANALYSIS")

        title_w = c.stringWidth("MEDICAL REPORT ANALYSIS", "Helvetica-Bold", 12)
        c.setStrokeColor(TEAL)
        c.setLineWidth(1.2)
        c.line(w - 16 - title_w, h * 0.59, w - 16, h * 0.59)

        if self.report_date:
            c.setFillColor(colors.HexColor("#A8D8DC"))
            c.setFont("Helvetica-Oblique", 8.5)
            c.drawRightString(w - 16, h * 0.42, f"Updated: {self.report_date}")

    def wrap(self, *args):
        return (self.bw, self.bh)


class SectionHeader(Flowable):
    def __init__(self, text, width):
        Flowable.__init__(self)
        self.text = text
        self.sw = width
        self.sh = 0.32 * inch

    def draw(self):
        c = self.canv
        c.setFillColor(TEAL)
        c.roundRect(0, 0, self.sw, self.sh, 4, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.rect(8, 7, 4, self.sh - 14, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(22, self.sh * 0.33, self.text.upper())

    def wrap(self, *args):
        return (self.sw, self.sh)


class FooterCanvas(SimpleDocTemplate):
    def handle_pageEnd(self):
        self.canv.saveState()
        w, _ = letter
        self.canv.setStrokeColor(BORDER_GREY)
        self.canv.setLineWidth(0.5)
        self.canv.line(0.65*inch, 0.55*inch, w - 0.65*inch, 0.55*inch)
        self.canv.setFont("Helvetica-Oblique", 7)
        self.canv.setFillColor(STEEL)
        self.canv.drawString(0.65*inch, 0.38*inch,
            "CONFIDENTIAL — For authorised medical personnel only. Not for redistribution.")
        self.canv.setFont("Helvetica", 7)
        self.canv.drawRightString(w - 0.65*inch, 0.38*inch, f"Page {self.page}")
        self.canv.restoreState()
        SimpleDocTemplate.handle_pageEnd(self)


def make_styles():
    base = getSampleStyleSheet()
    s = {}
    s["body"] = ParagraphStyle("body", parent=base["Normal"], fontName="Helvetica", fontSize=9, textColor=DARK_TEXT, leading=14, spaceAfter=4)
    s["body_bold"] = ParagraphStyle("body_bold", parent=s["body"], fontName="Helvetica-Bold")
    s["label"] = ParagraphStyle("label", parent=s["body"], fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY)
    s["summary_body"] = ParagraphStyle("summary_body", parent=s["body"], fontSize=9, leading=15, alignment=TA_JUSTIFY, textColor=DARK_TEXT)
    s["finding_item"] = ParagraphStyle("finding_item", parent=s["body"], fontSize=9, leading=14, leftIndent=12, spaceAfter=3, textColor=DARK_TEXT)
    s["rec_body"] = ParagraphStyle("rec_body", parent=s["body"], fontSize=9.5, leading=16, alignment=TA_JUSTIFY, textColor=DARK_TEXT, leftIndent=8, rightIndent=8)
    s["table_header"] = ParagraphStyle("table_header", parent=s["body"], fontName="Helvetica-Bold", fontSize=8.5, textColor=WHITE, alignment=TA_CENTER)
    s["table_cell"] = ParagraphStyle("table_cell", parent=s["body"], fontSize=8.5, alignment=TA_CENTER)
    s["cat_label"] = ParagraphStyle("cat_label", parent=s["body"], fontName="Helvetica-Bold", fontSize=9, textColor=MID_BLUE, spaceAfter=3, spaceBefore=6)
    s["info_key"] = ParagraphStyle("info_key", parent=s["body"], fontName="Helvetica-Bold", fontSize=8.5, textColor=STEEL)
    s["info_val"] = ParagraphStyle("info_val", parent=s["body"], fontSize=8.5, textColor=DARK_TEXT)
    return s


def status_color(status: str):
    s = (status or "").lower()
    if s in ("high", "low", "abnormal", "critical", "elevated", "deficient"):
        return RED_ALERT
    if s in ("borderline", "marginal", "slightly high", "slightly low", "watch"):
        return AMBER
    return GREEN_OK


def status_badge(status: str):
    return status_color(status), WHITE


def _filter_category_summaries(category_summary: dict) -> dict:
    return {cat: text for cat, text in (category_summary or {}).items() if text and str(text).strip()}


def generate_pdf(data: dict, logo_path: str = None) -> io.BytesIO:
    buffer = io.BytesIO()
    MARGIN = 0.65 * inch
    PAGE_W, _ = letter
    CONTENT_W = PAGE_W - 2 * MARGIN

    doc = FooterCanvas(buffer, pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.4*inch, bottomMargin=0.75*inch)

    styles = make_styles()
    story = []
    now_str = datetime.now().strftime("%d %b %Y  |  %I:%M %p")

    story.append(HeaderBanner(logo_path, CONTENT_W, now_str))
    story.append(Spacer(1, 14))

    parameters = data.get("parameters", []) or []
    if parameters:
        story.append(SectionHeader("01  |  Laboratory Parameters", CONTENT_W))
        story.append(Spacer(1, 8))

        grouped = {}
        for p in parameters:
            cat = p.get("category", "general").lower()
            grouped.setdefault(cat, []).append(p)

        has_ref_range = any(p.get("reference_range") or p.get("ref_range") for p in parameters)

        if has_ref_range:
            col_w = [CONTENT_W * 0.32, CONTENT_W * 0.16, CONTENT_W * 0.12, CONTENT_W * 0.20, CONTENT_W * 0.20]
            header_row = [
                Paragraph("Parameter", styles["table_header"]),
                Paragraph("Value", styles["table_header"]),
                Paragraph("Unit", styles["table_header"]),
                Paragraph("Reference Range", styles["table_header"]),
                Paragraph("Status", styles["table_header"]),
            ]
        else:
            col_w = [CONTENT_W * 0.45, CONTENT_W * 0.20, CONTENT_W * 0.15, CONTENT_W * 0.20]
            header_row = [
                Paragraph("Parameter", styles["table_header"]),
                Paragraph("Value", styles["table_header"]),
                Paragraph("Unit", styles["table_header"]),
                Paragraph("Status", styles["table_header"]),
            ]

        for cat in CATEGORY_ORDER:
            params = grouped.get(cat, [])
            if not params:
                continue

            story.append(Paragraph(f"▸  {CATEGORY_LABELS.get(cat, cat.title())}", styles["cat_label"]))
            table_rows = [header_row]
            row_commands = []

            for idx, p in enumerate(params, start=1):
                name = p.get("name", "—")
                value = str(p.get("value", "—"))
                unit = p.get("unit", "—")
                ref_range = p.get("reference_range", p.get("ref_range", ""))
                status_str = p.get("status", "normal")
                s_bg, _ = status_badge(status_str)

                name_para = Paragraph(f"<b>{name}</b>", ParagraphStyle("np", parent=styles["table_cell"], alignment=TA_LEFT))
                value_para = Paragraph(f"<b>{value}</b>", ParagraphStyle("vp", parent=styles["table_cell"], fontName="Helvetica-Bold", textColor=status_color(status_str)))
                unit_para = Paragraph(unit, styles["table_cell"])
                status_para = Paragraph(f'<font color="white"><b>{status_str.upper()}</b></font>', styles["table_cell"])

                row = [name_para, value_para, unit_para]
                if has_ref_range:
                    row.append(Paragraph(ref_range or "—", styles["table_cell"]))
                row.append(status_para)
                table_rows.append(row)

                row_bg = LIGHT_GREY if idx % 2 == 0 else WHITE
                last_col = len(row) - 1
                row_commands.append(("BACKGROUND", (0, idx), (last_col - 1, idx), row_bg))
                row_commands.append(("BACKGROUND", (last_col, idx), (last_col, idx), s_bg))

            t = Table(table_rows, colWidths=col_w, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0),(-1,0), NAVY),
                ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE", (0,0),(-1,0), 8.5),
                ("TEXTCOLOR", (0,0),(-1,0), WHITE),
                ("ALIGN", (0,0),(-1,-1), "CENTER"),
                ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING", (0,0),(-1,-1), 6),
                ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                ("LEFTPADDING", (0,0),(-1,-1), 6),
                ("RIGHTPADDING", (0,0),(-1,-1), 6),
                ("ALIGN", (0,1),(0,-1), "LEFT"),
                ("LEFTPADDING", (0,1),(0,-1), 10),
                ("GRID", (0,0),(-1,-1), 0.4, BORDER_GREY),
                ("LINEBELOW", (0,0),(-1,0), 1.5, TEAL),
            ] + row_commands))
            story.append(KeepTogether(t))
            story.append(Spacer(1, 10))

        story.append(Spacer(1, 6))

    category_summary = _filter_category_summaries(data.get("category_summary", {}))
    key_findings = data.get("key_findings", []) or []

    if category_summary or key_findings:
        story.append(SectionHeader("02  |  Diagnostic Summary", CONTENT_W))
        story.append(Spacer(1, 10))

        for cat, summary_text in category_summary.items():
            sum_row = [[
                Paragraph(CATEGORY_LABELS.get(cat, cat.title()), styles["label"]),
                Paragraph(summary_text, styles["summary_body"]),
            ]]
            sum_table = Table(sum_row, colWidths=[CONTENT_W*0.22, CONTENT_W*0.78])
            sum_table.setStyle(TableStyle([
                ("VALIGN", (0,0),(-1,-1), "TOP"),
                ("TOPPADDING", (0,0),(-1,-1), 5),
                ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                ("LEFTPADDING", (0,0),(0,-1), 8),
                ("BACKGROUND", (0,0),(0,-1), LIGHT_TEAL),
                ("LINEAFTER", (0,0),(0,-1), 1.2, TEAL),
                ("LINEBELOW", (0,0),(-1,-1), 0.4, BORDER_GREY),
            ]))
            story.append(sum_table)

        if key_findings:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Key Findings", ParagraphStyle(
                "kf_hd", parent=styles["body_bold"], fontSize=9.5, textColor=NAVY, spaceBefore=4, spaceAfter=6)))
            for finding in key_findings:
                story.append(Paragraph(f"◆  {finding}", styles["finding_item"]))
            story.append(Spacer(1, 8))

    recommendation = data.get("recommendation", "")
    if recommendation:
        story.append(Spacer(1, 4))
        story.append(SectionHeader("03  |  Clinical Recommendation", CONTENT_W))
        story.append(Spacer(1, 10))

        rec_inner = [
            [Paragraph("⚕  Physician's Note", ParagraphStyle("rec_hd", parent=styles["body_bold"], fontSize=9, textColor=TEAL, spaceAfter=4))],
            [Paragraph(recommendation, styles["rec_body"])],
        ]
        rec_table = Table(rec_inner, colWidths=[CONTENT_W])
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), LIGHT_TEAL),
            ("BOX", (0,0),(-1,-1), 1.5, TEAL),
            ("LINEBEFORE", (0,0),(0,-1), 5, TEAL),
            ("TOPPADDING", (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 8),
            ("LEFTPADDING", (0,0),(-1,-1), 14),
            ("RIGHTPADDING", (0,0),(-1,-1), 14),
        ]))
        story.append(rec_table)
        story.append(Spacer(1, 12))

    story.append(HRFlowable(width=CONTENT_W, thickness=0.5, color=BORDER_GREY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report is generated by an AI-assisted diagnostic system and is intended solely for use by "
        "qualified healthcare professionals. Results should be interpreted in conjunction with clinical "
        "findings, patient history, and physician judgment. This document does not constitute a medical "
        "diagnosis. Please consult your physician before making any health-related decisions.",
        ParagraphStyle("disc", parent=styles["body"], fontSize=7.2, textColor=STEEL, leading=11, alignment=TA_JUSTIFY)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
