"""
IndusVision Backend - Predictive Maintenance Service
=======================================================
A lightweight rule-based health scoring model that runs on every sensor reading,
plus a hook for the trained XGBoost/Random Forest model (Module 5) once you have
enough historical data logged to train on.

HOW TO UPGRADE TO A TRAINED ML MODEL:
  1. Export sensor_readings from MongoDB to CSV once you have weeks of data + labeled
     failure events (see /api/reports/export for a ready-made export endpoint).
  2. Train a RandomForestClassifier / XGBClassifier on features:
     [temperature, vibration, current_amps, gas_raw, rolling averages] -> label: failure within N days.
  3. Save the trained model as maintenance_model.pkl in backend/app/ml_models/.
  4. Replace `calculate_health_score()` below with: load the pickle, call .predict_proba().
This keeps the rest of the codebase (routes, dashboard) unchanged when you upgrade.
"""
from datetime import datetime, timedelta, timezone


def calculate_health_score(reading: dict) -> dict:
    """
    Rule-based health scoring (0-100). Penalizes each out-of-range signal.
    Returns health_score, failure_probability, predicted_status, remaining_useful_life_days.
    """
    score = 100.0
    reasons = []

    temp = reading.get("temperature", -1)
    if temp is not None and temp > 75:
        penalty = min(30, (temp - 75) * 2)
        score -= penalty
        reasons.append(f"high temperature ({temp:.1f} °C; threshold 75 °C)")

    if reading.get("vibration", 0) == 1:
        score -= 20
        reasons.append(f"abnormal vibration (sensor value {reading.get('vibration')})")

    current = reading.get("current_amps", 0)
    if current > 15:
        penalty = min(25, (current - 15) * 3)
        score -= penalty
        reasons.append(f"overcurrent ({current:.2f} A; threshold 15 A)")

    gas = reading.get("gas_raw", 0)
    if gas > 2000:
        score -= 15
        reasons.append(f"elevated gas/smoke reading ({gas}; threshold 2000)")

    distance = reading.get("distance_cm", -1)
    if distance is not None and 0 <= distance < 30:
        score -= 20
        reasons.append(f"obstacle dangerously close ({distance:.1f} cm; threshold 30 cm)")

    # The ESP32 also reports a combined fault flag. Preserve the event even if
    # the individual sensor values do not match one of the rules above.
    if reading.get("fault") and not reasons:
        reasons.append("ESP32 reported a fault; no individual sensor threshold identified the cause")

    score = max(0.0, min(100.0, score))
    failure_probability = round((100 - score) / 100, 2)

    if score >= 80:
        predicted_status = "normal"
        remaining_days = 90
    elif score >= 50:
        predicted_status = "warning"
        remaining_days = 14
    else:
        predicted_status = "failure"
        remaining_days = 2

    # Any configured out-of-range measurement is an actionable event even if
    # its score penalty alone leaves the aggregate score in the normal band.
    if reasons and predicted_status == "normal":
        predicted_status = "warning"
        remaining_days = 14

    if reading.get("fault"):
        predicted_status = "failure"
        remaining_days = 2

    return {
        "health_score": round(score, 1),
        "failure_probability": failure_probability,
        "predicted_status": predicted_status,
        "remaining_useful_life_days": remaining_days,
        "next_maintenance_date": datetime.now(timezone.utc) + timedelta(days=remaining_days),
        "reasons": reasons,
        "generated_at": datetime.now(timezone.utc),
    }
