import logging

from google import genai

from app.config import settings

logger = logging.getLogger(__name__)
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set."
        )
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def _generate(prompt: str) -> str:
    """Call Gemini asynchronously and convert provider errors to a useful API error."""
    try:
        response = await _get_client().aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")
        return response.text.strip()
    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception("Gemini API request failed model=%s", settings.GEMINI_MODEL)
        raise RuntimeError(
            f"Gemini request failed for model '{settings.GEMINI_MODEL}'. "
            "Check that the model is available and GEMINI_API_KEY is valid."
        ) from exc


async def generate_machine_health_summary(machine_id: str, recent_readings: list, prediction: dict | None) -> str:
    """Turn recent sensor history and the maintenance prediction into a concise summary."""
    prompt = f"""You are an industrial maintenance analyst. Given the recent sensor readings and
predictive-maintenance output for machine {machine_id}, write a concise (3-4 sentence) plain-English
summary for a plant supervisor. Mention any concerning trend and a concrete recommended action.
Do not invent numbers that are not in the data below.

Recent readings (most recent last):
{recent_readings}

Predictive maintenance model output:
{prediction}
"""
    return await _generate(prompt)


async def generate_safety_report_narrative(violations: list, period_label: str) -> str:
    """Create a report narrative from the recorded PPE violation events."""
    prompt = f"""You are a workplace safety officer writing the narrative section of a {period_label}
safety report. Given this list of PPE violation detections (class name, zone, timestamp), write a
professional 4-6 sentence summary: total counts, most common violation type, any zone/time pattern,
and one actionable recommendation. Do not invent data not present below.

Violations:
{violations}
"""
    return await _generate(prompt)


async def chat_with_assistant(user_message: str, context: str = "") -> str:
    """Answer dashboard questions using only the supplied operational context."""
    prompt = f"""You are the IndusVision plant-operations assistant. Answer the user's question using
only the context provided. If the context doesn't contain the answer, say so plainly instead of guessing.

Context:
{context}

Question: {user_message}
"""
    return await _generate(prompt)
