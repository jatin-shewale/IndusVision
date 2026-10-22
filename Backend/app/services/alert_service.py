"""Create persistent alerts and send structured critical-alert emails."""
import html
import logging
import smtplib
import asyncio
from datetime import datetime, timezone
from email.message import EmailMessage
from fastapi import BackgroundTasks

from app.config import settings
from app.database import alerts_collection

logger = logging.getLogger(__name__)


async def create_alert(
    title: str,
    message: str,
    severity: str,
    source: str,
    machine_id: str | None = None,
    deduplicate_open: bool = False,
    background_tasks: BackgroundTasks | None = None,
) -> dict:
    should_email = severity == "critical" or (severity == "warning" and source in {"sensor", "detection"})
    email_enabled = bool(settings.SMTP_USERNAME and settings.ALERT_EMAIL_TO)
    if deduplicate_open:
        existing = await alerts_collection.find_one({
            "title": title,
            "source": source,
            "machine_id": machine_id,
            "status": "open",
        })
        if existing:
            now = datetime.now(timezone.utc)
            await alerts_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"message": message, "last_event_at": now}},
            )
            # An alert created before email delivery was enabled may still be
            # open. Queue one notification for it, without mailing every frame.
            if should_email and email_enabled and not existing.get("email_queued_at"):
                queued = await alerts_collection.update_one(
                    {"_id": existing["_id"], "email_queued_at": {"$exists": False}},
                    {"$set": {"email_queued_at": now}},
                )
                if queued.modified_count:
                    _queue_alert_email(
                        background_tasks, title, message, severity, source,
                        machine_id, existing.get("created_at", now),
                    )
            existing["id"] = str(existing.pop("_id"))
            existing["message"] = message
            return existing

    created_at = datetime.now(timezone.utc)
    doc = {
        "title": title,
        "message": message,
        "severity": severity,
        "source": source,
        "machine_id": machine_id,
        "status": "open",
        "created_at": created_at,
    }
    result = await alerts_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)

    if should_email:
        if email_enabled:
            await alerts_collection.update_one(
                {"_id": result.inserted_id}, {"$set": {"email_queued_at": created_at}}
            )
            _queue_alert_email(background_tasks, title, message, severity, source, machine_id, created_at)
        else:
            logger.warning("Skipping alert email because SMTP_USERNAME or ALERT_EMAIL_TO is not configured")

    return doc


def _queue_alert_email(
    background_tasks: BackgroundTasks | None,
    title: str,
    details: str,
    severity: str,
    source: str,
    machine_id: str | None,
    created_at: datetime,
) -> None:
    args = (title, details, severity, source, machine_id, created_at)
    if background_tasks is not None:
        background_tasks.add_task(_send_email_alert, *args)
    else:
        # Non-route callers still must not block an async request on SMTP.
        asyncio.create_task(asyncio.to_thread(_send_email_alert, *args))


def _send_email_alert(
    title: str,
    details: str,
    severity: str,
    source: str,
    machine_id: str | None,
    created_at: datetime,
) -> None:
    """Send a best-effort email; missing SMTP settings never block ingestion."""
    if not settings.SMTP_USERNAME or not settings.ALERT_EMAIL_TO:
        logger.warning("Skipping alert email because SMTP_USERNAME or ALERT_EMAIL_TO is not configured")
        return

    recommendations = {
        "sensor": "Inspect the sensor readings and the named sensor/wiring. Check the machine before returning it to normal operation.",
        "detection": "Check the listed camera or zone and ensure affected workers wear the required PPE. Have a supervisor verify the area.",
        "inventory": "Review the affected inventory item and arrange replenishment if needed.",
    }
    recommendation = recommendations.get(
        source, "Review this alert in the IndusVision dashboard and take the appropriate corrective action."
    )
    timestamp = created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    location = machine_id or "Not specified"
    source_label = source.replace("_", " ").title()
    safe_title = html.escape(title)
    safe_source = html.escape(source_label)
    safe_location = html.escape(location)
    safe_timestamp = html.escape(timestamp)
    safe_severity = html.escape(severity.upper())
    safe_details = html.escape(details.strip() or "No additional event details were provided.")
    safe_recommendation = html.escape(recommendation)
    subject = f"[IndusVision][{severity.upper()}][{source.upper()}] {title}"

    text_body = "\n".join([
        "INDUSVISION | ALERT NOTIFICATION",
        "=" * 34,
        "",
        "An event requiring attention has been recorded.",
        "",
        f"Alert: {title}",
        f"Severity: {severity.upper()}",
        f"Source: {source_label}",
        f"Machine / Zone: {location}",
        f"Detected at: {timestamp}",
        "",
        "CAUSE AND EVENT DETAILS",
        details.strip() or "No additional event details were provided.",
        "",
        "RECOMMENDED ACTION",
        recommendation,
        "",
        "This is an automated notification. Review and acknowledge the event in the IndusVision Alerts dashboard.",
    ])
    html_body = f"""<html><body style="font-family:Arial,sans-serif;color:#17202a;line-height:1.5">
      <div style="max-width:680px;margin:auto;border:1px solid #d8dee4;border-radius:8px;overflow:hidden">
        <div style="background:#17202a;color:#fff;padding:18px 24px">
          <div style="font-size:12px;letter-spacing:1px;color:#f0a202">INDUSVISION ALERT NOTIFICATION</div>
          <h2 style="margin:8px 0 0">{safe_title}</h2>
        </div>
        <div style="padding:20px 24px">
          <table style="border-collapse:collapse;width:100%">
            <tr><td style="padding:6px;color:#667085">Severity</td><td style="padding:6px"><strong>{safe_severity}</strong></td></tr>
            <tr><td style="padding:6px;color:#667085">Source</td><td style="padding:6px">{safe_source}</td></tr>
            <tr><td style="padding:6px;color:#667085">Machine / Zone</td><td style="padding:6px">{safe_location}</td></tr>
            <tr><td style="padding:6px;color:#667085">Detected at</td><td style="padding:6px">{safe_timestamp}</td></tr>
          </table>
          <h3 style="margin:22px 0 6px">Cause and event details</h3>
          <div style="background:#f6f8fa;padding:12px 16px;border-radius:5px;white-space:pre-wrap">{safe_details}</div>
          <h3 style="margin:22px 0 6px">Recommended action</h3>
          <p>{safe_recommendation}</p>
          <p style="color:#667085;font-size:12px;border-top:1px solid #d8dee4;padding-top:12px">Automated notification. Review and acknowledge this event in the IndusVision Alerts dashboard.</p>
        </div>
      </div>
    </body></html>"""

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USERNAME
        msg["To"] = settings.ALERT_EMAIL_TO
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("alert_email_sent source=%s severity=%s title=%s", source, severity, title)
    except Exception:
        logger.exception("Could not send alert email for alert=%s", title)
