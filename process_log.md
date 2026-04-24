# Process Log

**Name**: Attahiru Jibril
**Date**: 2026-04-24

---

## Hour 1

- Designed the overall system architecture
- Set up project with `uv`, created directory skeleton
- Reviewed seed data in `res/curriculum_seed.json` (12 items across 5 skills: counting, number_sense, addition, subtraction, word_problem) and designed expansion rules per skill
- Used Claude Code to write `scripts/generate_data.py`, expanding the seed to 60 curriculum items

```text
Write scripts/generate_data.py that reads res/curriculum_seed.json and expands
it to 60+ items. Skills: counting (objects 1-10, 6 object types), number_sense
(compare pairs + before/after), addition (simple sums + Rwandan word problems
with mangoes/cows/RWF), subtraction (take-away + basket/market context),
word_problem (RWF, water point, mandazi contexts). Each item: id, skill,
difficulty 1-9, age_band, stem_en/fr/kin, visual ref string, answer_int,
distractors [answer-1, answer+1, answer+2] clamped to [0,20], hint_en, hint_kin.
Output: data/curriculum_full.json.
```

---

## Hour 2

- Wrote `tutor/curriculum_loader.py`
- Implemented `tutor/visual.py` — `parse_visual("apples_5")` → `{"shape": "apples", "count": 5, "layout": "scatter"}` with row layout for fingers/beads
- Created `frontend/index.html` `ActivityScreen` to use `visual_meta` from API (falls back to parsing `item.visual` directly), renders scatter vs row layouts with `popIn` animations

```text
Implement the visual module. create tutor/visual.py backend metadata parser
and frontend/index.html ActivityScreen to use emoji-based dynamic rendering
with scatter/row layouts and popIn animations instead of static PNGs.
```

---

## Hour 3

- Implemented `tutor/asr_adapt.py` — Whisper-tiny INT8 ONNX transcriber with child-voice adaptation, number extraction, response scoring
- Added `tutor/lang_detect.py` — KIN/FR/EN/mix detection with token dictionaries and mixed-language handling
- Created `tutor/feedback.py` — multilingual feedback pool (KIN/FR/EN) with correct/incorrect/hint/encouragement templates
- Built `tutor/progress_store.py` — encrypted SQLite with Fernet, students/attempts/bkt_state/elo_state tables, DP sync
- Implemented `tutor/adaptive.py` — BKT knowledge tracing + Elo baseline, adaptive engine with mastery threshold 0.90
- Added `tutor/tts_engine.py` — Piper TTS primary with pyttsx3 fallback, WAV caching
- Wrote `scripts/download_model.py` to export and quantize Whisper-tiny to INT8 ONNX (~45 MB)

```text
Implement ASR with Whisper-tiny INT8 ONNX for child voices. Add lang_detect
for KIN/FR/EN/mix. Create feedback.py, progress_store.py with encrypted
SQLite, adaptive.py with BKT + Elo, tts_engine.py with Piper. Write
scripts/download_model.py to get INT8 quantized model.
```

---

## Hour 4

- Built complete frontend with `frontend/index.jsx` — ProfileScreen, ActivityScreen, FeedbackScreen, ReportScreen, WelcomeScreen, Stars, ProgressBar
- Added `frontend/js/utils/emoji.js` for visual rendering, `audio.js` for mic recording
- Implemented `frontend/js/api.js` for backend communication
- Set up Vite build with `vite.config.js`, `package.json`, `index.html`
- Added `frontend/src/index.css` with consistent styling for all components
- Integrated i18n support via `frontend/src/i18n.js` (KIN/FR/EN)

```text
Build React frontend with Vite: Profile, Activity, Feedback, Report,
Welcome screens. Add emoji utils, audio recording, API layer, i18n
support, and CSS styling. Use JSX components with hooks.
```

---
