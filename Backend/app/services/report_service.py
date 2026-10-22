"""
IndusVision Backend - Report Generation Service (PDF / Excel / CSV)
"""
import io
import csv
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl


def build_pdf_report(title: str, summary_text: str, rows: list[dict]) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(title, styles["Title"]),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(summary_text, styles["BodyText"]),
        Spacer(1, 12),
    ]

    if rows:
        headers = list(rows[0].keys())
        table_data = [headers] + [[str(r.get(h, "")) for h in headers] for r in rows]
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ]))
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def build_excel_report(title: str, rows: list[dict]) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:31] if title else "Report"

    if rows:
        headers = list(rows[0].keys())
        ws.append(headers)
        for r in rows:
            ws.append([r.get(h, "") for h in headers])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def build_csv_report(rows: list[dict]) -> io.StringIO:
    buffer = io.StringIO()
    if rows:
        headers = list(rows[0].keys())
        writer = csv.DictWriter(buffer, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    buffer.seek(0)
    return buffer
