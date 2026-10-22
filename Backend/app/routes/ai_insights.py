"""
IndusVision Backend - AI Insights Routes (powered by Gemini)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import sensor_readings_collection, maintenance_collection
from app.core.dependencies import get_current_user
from app.services import gemini_service

router = APIRouter(prefix="/api/ai", tags=["AI Insights (Gemini)"])


class ChatRequest(BaseModel):
    message: str
    machine_id: str | None = None


@router.get("/machine-summary/{machine_id}")
async def machine_health_summary(machine_id: str, current_user: dict = Depends(get_current_user)):
    readings = await sensor_readings_collection.find({"machine_id": machine_id}) \
        .sort("timestamp", -1).limit(20).to_list(20)
    prediction = await maintenance_collection.find_one({"machine_id": machine_id}, sort=[("generated_at", -1)])

    if not readings:
        raise HTTPException(status_code=404, detail="No sensor data found for this machine")

    readings_clean = [{k: v for k, v in r.items() if k not in ("_id",)} for r in readings]
    prediction_clean = {k: v for k, v in (prediction or {}).items() if k not in ("_id",)}

    try:
        summary = await gemini_service.generate_machine_health_summary(machine_id, readings_clean, prediction_clean)
    except RuntimeError as e:
        status_code = (
            403 if "Google denied Gemini API access" in str(e)
            else 503 if "GEMINI_API_KEY is not set" in str(e)
            else 502
        )
        raise HTTPException(status_code=status_code, detail=str(e)) from e

    return {"machine_id": machine_id, "summary": summary}


@router.post("/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Backs the dashboard's 'Ask AI' box. Grounds the answer in that machine's recent data if given."""
    context = ""
    if request.machine_id:
        readings = await sensor_readings_collection.find({"machine_id": request.machine_id}) \
            .sort("timestamp", -1).limit(10).to_list(10)
        context = str([{k: v for k, v in r.items() if k != "_id"} for r in readings])

    try:
        answer = await gemini_service.chat_with_assistant(request.message, context)
    except RuntimeError as e:
        status_code = (
            403 if "Google denied Gemini API access" in str(e)
            else 503 if "GEMINI_API_KEY is not set" in str(e)
            else 502
        )
        raise HTTPException(status_code=status_code, detail=str(e)) from e

    return {"answer": answer}
