import logging
from datetime import datetime, timedelta
import re

from dateparser.search import search_dates

# try to import spaCy and a small multilingual NER model (fallback if not installed)
try:
    import spacy

    try:
        _spacy_nlp = spacy.load("xx_ent_wiki_sm")
        logging.getLogger("nlp").info("spaCy model xx_ent_wiki_sm loaded")
    except Exception:
        # model not installed / load failed
        _spacy_nlp = None
        logging.getLogger("nlp").info("spaCy model xx_ent_wiki_sm not available, falling back to regex")
except Exception:
    _spacy_nlp = None

logger = logging.getLogger("nlp")

def _to_iso(dt):
    return dt.isoformat() if isinstance(dt, datetime) else None

def _extract_location_by_spacy(text: str):
    """
    Use spaCy NER (if available) to find location-like entities.
    Returns first reasonable candidate or None.
    """
    if not _spacy_nlp:
        return None
    try:
        doc = _spacy_nlp(text)
        # prefer GPE / LOC / FAC / ORG if present; fallback to any LOC-like entity
        for ent in doc.ents:
            if ent.label_ in ("GPE", "LOC", "FAC", "ORG", "LOC_ORG"):
                cand = ent.text.strip()
                if cand:
                    return cand
        # last-resort: return first entity
        if doc.ents:
            return doc.ents[0].text.strip()
    except Exception as e:
        logger.debug("spaCy extraction error: %s", e)
    return None

def parse_date(text: str):
    """
    Return dict:
      {
        "event": str | None,
        "start_time": ISO str | None,
        "end_time": ISO str | None,
        "location": str | None,
        "reminder_minutes": int | None
      }

    Uses:
      - spaCy (xx_ent_wiki_sm) for location / entity hints if available
      - dateparser.search.search_dates for date/time recognition
      - regex heuristics for Vietnamese reminder phrases
    """
    if not text or not text.strip():
        return {"event": None, "start_time": None, "end_time": None, "location": None, "reminder_minutes": None}

    s = text.strip()

    # 1) detect & remove reminder phrase first so it isn't parsed as a date
    reminder_minutes = None
    rem_match = re.search(r'\bnhắc(?: tôi)?(?: (?:trước|trong))?\s+(\d+)\s*(phút|p|m|min)?\b', s, flags=re.I | re.U)
    if not rem_match:
        rem_match = re.search(r'\b(\d+)\s*(phút|p|m|min)\s+trước\b', s, flags=re.I | re.U)
    rem_phrase = None
    if rem_match:
        try:
            reminder_minutes = int(rem_match.group(1))
        except Exception:
            reminder_minutes = None
        rem_phrase = rem_match.group(0)
        s_for_dates = re.sub(re.escape(rem_phrase), "", s, flags=re.I)
    else:
        s_for_dates = s

    s_for_dates = s_for_dates.strip()

    # 2) use spaCy to extract location candidate (fallback to regex)
    location = _extract_location_by_spacy(s_for_dates)
    if not location:
        m_loc = re.search(r'\b(?:tại|ở)\s+([^\,\.\;\n]+)', s, flags=re.I | re.U)
        if m_loc:
            cand = m_loc.group(1).strip()
            cand = re.sub(r'\b(vào|nhắc|từ|đến|trong)\b.*$', '', cand, flags=re.I | re.U).strip(' ,.')
            if cand:
                location = cand

    # 3) find date/time matches on cleaned text (reminder removed)
    try:
        matches = search_dates(s_for_dates, languages=["vi", "en"], settings={"PREFER_DATES_FROM": "future"})
    except Exception:
        matches = None

    start_dt = None
    end_dt = None

    # explicit range detection ("từ ... đến ...")
    m_range = re.search(r'\b(?:từ|from)\s+(.+?)\s+(?:đến|to)\s+(.+?)(?:[\,\.\;]|$)', s_for_dates, flags=re.I | re.U)
    if m_range:
        try:
            r1 = search_dates(m_range.group(1), languages=["vi", "en"], settings={"PREFER_DATES_FROM": "future"})
            r2 = search_dates(m_range.group(2), languages=["vi", "en"], settings={"PREFER_DATES_FROM": "future"})
            if r1 and r2:
                start_dt = r1[0][1]
                end_dt = r2[0][1]
        except Exception:
            pass
    else:
        if matches and len(matches) > 0:
            start_dt = matches[0][1]
            if len(matches) > 1:
                cand = matches[1][1]
                # accept second match as end only if it's after start (avoid reminder/time-before)
                if isinstance(start_dt, datetime) and isinstance(cand, datetime) and cand > start_dt:
                    end_dt = cand

    # 4) derive event/title: remove date substrings, location and reminder phrases
    event = s_for_dates
    if matches:
        for match_text, _dt in matches:
            event = event.replace(match_text, "")

    if m_range:
        event = re.sub(r'\b(?:từ|from)\s+.+?\s+(?:đến|to)\s+.+?(?:\b|$)', '', event, flags=re.I | re.U)
    if location:
        # remove common location tokens occurrences
        event = re.sub(r'\b(?:tại|ở)\s+' + re.escape(location), '', event, flags=re.I | re.U)
    if rem_phrase:
        event = re.sub(re.escape(rem_phrase), '', event, flags=re.I)

    event = re.sub(r'\b(vào|vào lúc|hôm nay|ngày mai|sáng|chiều|tối|đêm|từ|đến|trong)\b', '', event, flags=re.I | re.U)
    event = re.sub(r'\s+', ' ', event).strip(' ,.-')

    return {
        "event": event or None,
        "start_time": _to_iso(start_dt),
        "end_time": _to_iso(end_dt),
        "location": location,
        "reminder_minutes": reminder_minutes,
    }