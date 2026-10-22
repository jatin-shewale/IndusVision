"""
IndusVision Backend - Report Routes (Module 8)
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.database import sensor_readings_collection, detections_collection, alerts_collection, inventory_collection
from app.core.dependencies import get_current_user
from app.services.report_service import build_pdf_report, build_excel_report, build_csv_report
from app.services.gemini_service import generate_safety_report_narrative

router = APIRouter(prefix="/api/reports", tags=["Reports"])

PERIOD_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


async def _get_violations(since: datetime) -> list[dict]:
    docs = await detections_collection.find(
        {"is_violation": True, "timestamp": {"$gte": since}}
    ).sort("timestamp", -1).to_list(1000)
    return [
        {"class": ", ".join(d["class_name"] for d in doc.get("detections", [])),
         "zone": doc.get("machine_zone", "-"),
         "timestamp": doc["timestamp"].strftime("%Y-%m-%d %H:%M")}
        for doc in docs
    ]


@router.get("/safety/{period}")
async def safety_report(period: str, fmt: str = "pdf", current_user: dict = Depends(get_current_user)):
    days = PERIOD_DAYS.get(period, 7)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    violations = await _get_violations(since)

    try:
        narrative = await generate_safety_report_narrative(violations, period)
    except RuntimeError:
        narrative = (f"Gemini API key not configured — showing raw data only. "
                     f"{len(violations)} PPE violations recorded in the last {days} day(s).")

    if fmt == "excel":
        buf = build_excel_report(f"Safety Report ({period})", violations)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                  headers={"Content-Disposition": f"attachment; filename=safety_report_{period}.xlsx"})
    if fmt == "csv":
        buf = build_csv_report(violations)
        return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                                  headers={"Content-Disposition": f"attachment; filename=safety_report_{period}.csv"})

    buf = build_pdf_report(f"IndusVision Safety Report ({period.title()})", narrative, violations)
    return StreamingResponse(buf, media_type="application/pdf",
                              headers={"Content-Disposition": f"attachment; filename=safety_report_{period}.pdf"})


@router.get("/inventory")
async def inventory_report(fmt: str = "excel", current_user: dict = Depends(get_current_user)):
    docs = await inventory_collection.find().to_list(1000)
    rows = [
        {"item_name": d["item_name"], "category": d["category"], "quantity": d["quantity"],
         "unit": d["unit"], "threshold": d["threshold"],
         "low_stock": "YES" if d["quantity"] <= d["threshold"] else "no"}
        for d in docs
    ]
    if fmt == "csv":
        buf = build_csv_report(rows)
        return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                                  headers={"Content-Disposition": "attachment; filename=inventory_report.csv"})
    if fmt == "pdf":
        buf = build_pdf_report("IndusVision Inventory Report", f"{len(rows)} items tracked.", rows)
        return StreamingResponse(buf, media_type="application/pdf",
                                  headers={"Content-Disposition": "attachment; filename=inventory_report.pdf"})

    buf = build_excel_report("Inventory", rows)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              headers={"Content-Disposition": "attachment; filename=inventory_report.xlsx"})


@router.get("/sensor-history/{machine_id}")
async def export_sensor_history_csv(machine_id: str, current_user: dict = Depends(get_current_user)):
    """
    Export raw sensor history as CSV — feed this into training a real ML model
    for Module 5 (see predictive_maintenance.py's upgrade instructions).
    """
    docs = await sensor_readings_collection.find({"machine_id": machine_id}) \
        .sort("timestamp", 1).to_list(100000)
    rows = [
        {"timestamp": d["timestamp"].isoformat(), "temperature": d.get("temperature"),
         "humidity": d.get("humidity"), "vibration": d.get("vibration"),
         "current_amps": d.get("current_amps"), "gas_raw": d.get("gas_raw"),
         "distance_cm": d.get("distance_cm"), "fault": d.get("fault")}
        for d in docs
    ]
    buf = build_csv_report(rows)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                              headers={"Content-Disposition": f"attachment; filename={machine_id}_sensor_history.csv"})
