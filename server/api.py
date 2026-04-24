"""FastAPI backend for AI Math Tutor."""

import io
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel

from reports import parent_report as pr
from tutor.adaptive import AdaptiveEngine
from tutor.curriculum_loader import load_curriculum
from tutor.feedback import get_feedback, get_hint
from tutor.lang_detect import detect_language
from tutor.progress_store import ProgressDB
from tutor.tts_engine import TTSEngine
from tutor.visual import parse_visual

logger = logging.getLogger(__name__)

# ── Pydantic request models ───────────────────────────────────────────────────


class SessionStartRequest(BaseModel):
    name: str
    lang: str = "en"
    icon: str = "star"


class SessionEndRequest(BaseModel):
    session_id: int


class TapAnswerRequest(BaseModel):
    student_id: str
    session_id: int
    item_id: str
    choice: int


# ── Helpers ───────────────────────────────────────────────────────────────────


def _restore_student_state(engine: AdaptiveEngine, db: ProgressDB, student_id: str):
    """Hydrate in-memory BKT state from the DB for a returning student."""
    bkt_state = db.load_bkt_state(student_id)
    if not bkt_state:
        return
    student_state = engine._students[student_id]
    for skill, data in bkt_state.items():
        if skill in student_state.bkt:
            student_state.bkt[skill].p_mastery = data["p_mastery"]
            student_state.bkt[skill].attempts = data["attempts"]


def _persist_student_state(engine: AdaptiveEngine, db: ProgressDB, student_id: str):
    """Flush in-memory BKT state to the DB after an update."""
    student_state = engine._students[student_id]
    for skill, bkt_model in student_state.bkt.items():
        db.save_bkt_state(student_id, skill, bkt_model.p_mastery, bkt_model.attempts)


def _item_by_id(curriculum: list, item_id: str) -> dict | None:
    return next((i for i in curriculum if i["id"] == item_id), None)


def _stem(item: dict, lang: str) -> str:
    return item.get(f"stem_{lang}") or item.get("stem_en", "")


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    curriculum = load_curriculum("data/curriculum_full.json")
    app.state.curriculum = curriculum
    app.state.engine = AdaptiveEngine(curriculum)
    app.state.db = ProgressDB("data/progress.db.enc")
    app.state.tts = TTSEngine()

    try:
        from tutor.asr_adapt import WhisperONNXTranscriber

        app.state.asr = WhisperONNXTranscriber()
        logger.info("ASR loaded OK")
    except Exception as exc:
        logger.warning("ASR unavailable (model not downloaded?): %s", exc)
        app.state.asr = None

    try:
        app.state.tts.prewarm(curriculum)
    except Exception as exc:
        logger.warning("TTS prewarm failed: %s", exc)

    yield

    app.state.db.close()
    logger.info("DB closed and encrypted.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="AI Math Tutor", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Session endpoints ─────────────────────────────────────────────────────────


@app.post("/session/start")
async def session_start(req: SessionStartRequest):
    db: ProgressDB = app.state.db
    engine: AdaptiveEngine = app.state.engine

    students = db.list_students()
    student = next((s for s in students if s["name"] == req.name), None)

    if student is None:
        student_id = db.create_student(req.name, req.lang, req.icon)
    else:
        student_id = student["id"]
        if student.get("lang_pref") != req.lang:
            db._conn.execute(
                "UPDATE students SET lang_pref=? WHERE id=?", (req.lang, student_id)
            )
            db._conn.commit()

    _restore_student_state(engine, db, student_id)
    session_id = db.start_session(student_id)

    bkt_state = db.load_bkt_state(student_id)
    total_prior_attempts = sum(v.get("attempts", 0) for v in bkt_state.values())
    diagnostic_mode = total_prior_attempts < 3

    return {
        "student_id": student_id,
        "session_id": session_id,
        "diagnostic_mode": diagnostic_mode,
        "name": req.name,
        "lang": req.lang,
    }


@app.post("/session/end")
async def session_end(req: SessionEndRequest):
    result = app.state.db.end_session(req.session_id)
    return {
        "items_done": result.get("item_count", 0),
        "correct": result.get("correct_count", 0),
    }


# ── Item endpoint ─────────────────────────────────────────────────────────────


@app.get("/item/next")
async def item_next(student_id: str, lang: str = "en"):
    engine: AdaptiveEngine = app.state.engine
    db: ProgressDB = app.state.db

    if student_id not in engine._students:
        _restore_student_state(engine, db, student_id)

    item = engine.next_item(student_id)
    visual_meta = parse_visual(item.get("visual", ""))

    return {
        **item,
        "visual_url": f"/images/{item.get('visual', '')}.png",
        "visual_meta": visual_meta,
        "tts_url": f"/tts/{lang}/{item['id']}",
        "stem_localized": _stem(item, lang),
    }


# ── Answer endpoints ──────────────────────────────────────────────────────────


@app.post("/answer/tap")
async def answer_tap(req: TapAnswerRequest):
    db: ProgressDB = app.state.db
    engine: AdaptiveEngine = app.state.engine
    tts: TTSEngine = app.state.tts

    item = _item_by_id(app.state.curriculum, req.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    correct = req.choice == item["answer_int"]

    engine.update(req.student_id, req.item_id, correct, 0)
    _persist_student_state(engine, db, req.student_id)

    student = db.get_student(req.student_id)
    lang = student.get("lang_pref", "en") if student else "en"
    child_name = student["name"] if student else "friend"

    db.record_attempt(
        req.student_id,
        req.item_id,
        item["skill"],
        item["difficulty"],
        correct,
        0,
        lang_detected=lang,
        method="tap",
        session_id=req.session_id,
    )

    feedback_text = get_feedback(correct, lang, child_name)
    tts.speak(feedback_text, lang)  # warms the cache

    return {
        "correct": correct,
        "answer_int": item["answer_int"],
        "feedback_text": feedback_text,
        "feedback_tts_url": f"/tts/{lang}/speak?text={feedback_text}",
        "mastery": engine.get_mastery_summary(req.student_id),
        "hint": get_hint(item, lang) if not correct else None,
    }


@app.post("/answer/voice")
async def answer_voice(
    student_id: str = Form(...),
    session_id: int = Form(...),
    item_id: str = Form(...),
    lang: str = Form("en"),
    audio: UploadFile = File(...),
):
    if app.state.asr is None:
        raise HTTPException(
            status_code=503, detail="ASR not available — model not downloaded"
        )

    import soundfile as sf
    from tutor.asr_adapt import score_response

    db: ProgressDB = app.state.db
    engine: AdaptiveEngine = app.state.engine
    tts: TTSEngine = app.state.tts

    item = _item_by_id(app.state.curriculum, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    audio_bytes = await audio.read()
    try:
        audio_np, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode audio: {exc}")

    transcribed = app.state.asr.transcribe(audio_np, int(sr), lang_hint=lang)
    detected_lang = detect_language(transcribed)
    correct = score_response(item, transcribed)

    engine.update(student_id, item_id, correct, 0)
    _persist_student_state(engine, db, student_id)

    student = db.get_student(student_id)
    child_name = student["name"] if student else "friend"
    reply_lang = lang if detected_lang == "mix" else detected_lang

    db.record_attempt(
        student_id,
        item_id,
        item["skill"],
        item["difficulty"],
        correct,
        0,
        lang_detected=detected_lang,
        method="voice",
        session_id=session_id,
    )

    feedback_text = get_feedback(correct, reply_lang, child_name)
    tts.speak(feedback_text, reply_lang)

    return {
        "correct": correct,
        "answer_int": item["answer_int"],
        "transcribed": transcribed,
        "detected_lang": detected_lang,
        "feedback_text": feedback_text,
        "feedback_tts_url": f"/tts/{reply_lang}/speak?text={feedback_text}",
        "mastery": engine.get_mastery_summary(student_id),
        "hint": get_hint(item, reply_lang) if not correct else None,
    }


# ── Static media endpoints ────────────────────────────────────────────────────


@app.get("/images/{visual_ref:path}")
async def serve_image(visual_ref: str):
    path = Path("data/images") / visual_ref
    if not path.suffix:
        path = path.with_suffix(".png")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(path), media_type="image/png")


@app.get("/tts/{lang}/{item_id}")
async def serve_tts(lang: str, item_id: str):
    tts: TTSEngine = app.state.tts

    # Special case: arbitrary text via ?text= query param (used by speak endpoint)
    # Route: /tts/{lang}/speak handled by FastAPI before this if declared first —
    # so item_id == "speak" only reaches here if that route didn't match.

    item = _item_by_id(app.state.curriculum, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    text = _stem(item, lang)
    if not text:
        raise HTTPException(status_code=404, detail="No stem for this language")

    audio_bytes = tts.speak(text, lang)
    if not audio_bytes:
        raise HTTPException(status_code=503, detail="TTS synthesis failed")

    return Response(content=audio_bytes, media_type="audio/wav")


@app.get("/tts/{lang}/speak")
async def speak_text(lang: str, text: str):
    """Synthesize arbitrary text for feedback/hints."""
    if not text:
        raise HTTPException(status_code=400, detail="text param required")
    audio_bytes = app.state.tts.speak(text, lang)
    if not audio_bytes:
        raise HTTPException(status_code=503, detail="TTS synthesis failed")
    return Response(content=audio_bytes, media_type="audio/wav")


# ── Report endpoints ──────────────────────────────────────────────────────────


@app.get("/report/{student_id}")
async def report_json(student_id: str):
    db: ProgressDB = app.state.db
    student = db.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    summary = db.get_week_summary(student_id)
    bkt_state = db.load_bkt_state(student_id)
    return pr.build_report_json(student_id, summary, bkt_state)


@app.get("/report/{student_id}/html", response_class=HTMLResponse)
async def report_html(student_id: str):
    db: ProgressDB = app.state.db
    student = db.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    summary = db.get_week_summary(student_id)
    bkt_state = db.load_bkt_state(student_id)
    report = pr.build_report_json(student_id, summary, bkt_state)
    return HTMLResponse(content=pr.build_report_html(student, summary, report))


@app.get("/report/{student_id}/voiced")
async def report_voiced(student_id: str, lang: str = "en"):
    db: ProgressDB = app.state.db
    student = db.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    summary = db.get_week_summary(student_id)
    bkt_state = db.load_bkt_state(student_id)
    report = pr.build_report_json(student_id, summary, bkt_state)
    text = pr.build_voiced_text(student["name"], report, lang)
    audio_bytes = app.state.tts.speak(text, lang)
    if not audio_bytes:
        raise HTTPException(status_code=503, detail="TTS synthesis failed")
    return Response(content=audio_bytes, media_type="audio/wav")


# ── Health ────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    tutor_dir = Path("tutor")
    footprint_mb = (
        sum(f.stat().st_size for f in tutor_dir.rglob("*") if f.is_file()) / 1e6
        if tutor_dir.exists()
        else 0.0
    )
    return {
        "status": "ok",
        "footprint_mb": round(footprint_mb, 2),
        "curriculum_items": len(app.state.curriculum),
        "asr_available": app.state.asr is not None,
    }
