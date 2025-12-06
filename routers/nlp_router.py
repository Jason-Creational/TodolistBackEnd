from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from nlp import parse_date

nlp_router = APIRouter()
logger = logging.getLogger("nlp_router")


class NLPRequest(BaseModel):
    text: str


class NLPResponse(BaseModel):
    event: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    reminder_minutes: int | None = None


@nlp_router.post("/", response_model=NLPResponse)
def parse_nlp(payload: NLPRequest):
    logger.debug("Received NLP request: %s", getattr(payload, "text", None))
    if not getattr(payload, "text", None):
        raise HTTPException(status_code=400, detail="text is required")
    try:
        res = parse_date(payload.text)
    except Exception as e:
        logger.exception("nlp.parse_date error: %s", e)
        raise HTTPException(status_code=500, detail="NLP parsing error")

    return {
        "event": res.get("event"),
        "start_time": res.get("start_time"),
        "end_time": res.get("end_time"),
        "location": res.get("location"),
        "reminder_minutes": res.get("reminder_minutes"),
    }