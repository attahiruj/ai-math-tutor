# AI Math Tutor — Early Numeracy Kid Learners

An offline, adaptive math tutor for children aged 5–9. It teaches counting, number sense, addition, subtraction, and word problems through visuals, audio, and voice or tap interaction. It runs fully on CPU, supports Kinyarwanda, French, and English, and adapts in real time to each learner using Bayesian Knowledge Tracing.

---

## Features

- **Adaptive engine** — BKT + Elo selects the next item at the child's current learning frontier
- **Multilingual** — handles KIN/FR/EN and code-switched input; replies in the dominant language
- **Voice + tap responses** — Whisper-tiny INT8 ONNX ASR for spoken answers; tap-only fallback always works
- **Visual grounding** — emoji-rendered scenes with OpenCV blob-count verification for counting items
- **Encrypted local storage** — Fernet-encrypted SQLite; progress never leaves the device in plaintext
- **Parent report** — icon-based weekly 1-pager (JSON + HTML) with QR code link to voiced summary
- **CPU-only, offline** — no GPU, no network required at inference time

---

## Project Structure

```text
ai-math-tutor/
├── data/
│   ├── curriculum_full.json      # 60-item curriculum (5 skills, difficulties 1–9)
│   ├── progress.db.enc           # Fernet-encrypted SQLite (runtime)
│   └── tts/                      # TTS cache (excluded from footprint)
├── frontend/
│   ├── package.json              # npm project configuration
│   ├── index.html                # child-facing single-page UI entry
│   ├── index.jsx                 # React tweak panel (loaded via Babel)
│   ├── js/
│   │   ├── app.js
│   │   ├── api.js
│   │   ├── components/
│   │   └── utils/
│   └── css/
├── res/                          # seed materials (read-only)
│   ├── curriculum_seed.json
│   ├── diagnostic_probes_seed.csv
│   ├── child_utt_sample_seed.csv
│   └── parent_report_schema.json
├── reports/
│   └── parent_report.py          # generates weekly 1-pager from local DB
├── scripts/
│   ├── download_model.py         # exports + quantizes Whisper-tiny to INT8 ONNX
│   ├── generate_data.py          # generates curriculum_full.json + images/
│   └── gen_child_audio.py        # pitch-shifts Common Voice clips for child ASR
├── server/
│   └── api.py                    # FastAPI application
├── tutor/
│   ├── adaptive.py               # BKTModel, EloBaseline, AdaptiveEngine
│   ├── asr_adapt.py              # WhisperONNXTranscriber + extract_number + score_response
│   ├── curriculum_loader.py      # load_curriculum, get_items, load_probes
│   ├── feedback.py               # multilingual feedback templates
│   ├── lang_detect.py            # KIN/FR/EN/mix detection and reply routing
│   ├── models/                   # ONNX model files (downloaded separately)
│   ├── progress_store.py         # ProgressDB (encrypted SQLite + DP export)
│   ├── tts_engine.py             # TTSEngine (pyttsx3 with WAV cache)
│   └── visual.py                 # parse_visual + OpenCV blob counter
├── kt_eval.ipynb                 # BKT vs GRU vs Elo AUC evaluation
├── main.py                       # entry point → uvicorn server.api:app
├── footprint_report.md
└── pyproject.toml
```

---

## Setup

Requires **Python 3.12+** and [`uv`](https://github.com/astral-sh/uv).

### 1. Install dependencies

```bash
uv sync
```

### 2. Download the ASR model

Exports `openai/whisper-tiny` from HuggingFace and quantizes it to INT8 ONNX (~40–45 MB). Falls back to a pre-quantized build from `onnx-community/whisper-tiny` if export fails.

```bash
uv run python scripts/download_model.py
```

### 3. Generate the curriculum (optional — already committed)

Regenerates `data/curriculum_full.json` (60 items) and `data/images/*.png`:

```bash
uv run python scripts/generate_data.py
```

### 4. Start the backend server

```bash
uv run python main.py
```

The API is now live at `http://localhost:8000`.

### 5. Start the frontend

Install frontend dependencies and launch the Vite development server:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at the local URL displayed in the terminal (typically `http://localhost:5173`).

### 6. Run the Gradio demo (optional)

Launch the child-facing Gradio demo with microphone input:

```bash
pip install gradio requests
python demo.py
```

The demo will be available at `http://localhost:7860`.

---

## Models Used

| Model                         | Purpose                                                  | Source                                                            |
| ----------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------- |
| `openai/whisper-tiny`         | ASR for voice input (child-adapted, pitch-shifted -4 st) | [HuggingFace](https://huggingface.co/openai/whisper-tiny)         |
| `onnx-community/whisper-tiny` | Pre-quantized INT8 ONNX fallback                         | [HuggingFace](https://huggingface.co/onnx-community/whisper-tiny) |
| WhisperTokenizer              | Tokenizer for ASR decoding                               | Loaded from `tutor/models/whisper-tiny-fp32/`                     |

The ASR model is quantized to INT8 ONNX format (~40-45 MB) for CPU-only inference. Child voices are adapted by shifting pitch down 4 semitones before inference.

---

## API Endpoints

| Method | Path                        | Description                                                                       |
| ------ | --------------------------- | --------------------------------------------------------------------------------- |
| `POST` | `/session/start`            | `{name, lang, icon}` → `{student_id, session_id}`                                 |
| `POST` | `/session/end`              | `{session_id}` → `{items_done, correct}`                                          |
| `GET`  | `/item/next`                | `?student_id=&lang=` → next adaptive item                                         |
| `POST` | `/answer/tap`               | `{student_id, session_id, item_id, choice}` → `{correct, feedback_text, mastery}` |
| `POST` | `/answer/voice`             | multipart audio → same as tap + `{transcribed, detected_lang}`                    |
| `GET`  | `/images/{visual_ref}`      | serves PNG from `data/images/`                                                    |
| `GET`  | `/tts/{lang}/{item_id}`     | serves cached WAV                                                                 |
| `GET`  | `/report/{student_id}`      | JSON weekly report                                                                |
| `GET`  | `/report/{student_id}/html` | icon-based HTML parent report                                                     |
| `GET`  | `/health`                   | `{status, footprint_mb}`                                                          |

---

## Curriculum

60 items across 5 skills and difficulties 1–9, with trilingual stems (EN/FR/KIN):

| Skill          | Difficulties | Count | Context                                           |
| -------------- | ------------ | ----- | ------------------------------------------------- |
| `counting`     | 1–3          | 12    | Objects 1–10: apples, goats, stars, fish, fingers |
| `number_sense` | 3–7          | 12    | Comparisons, before/after on number line          |
| `addition`     | 3–7          | 12    | Sums 1+1 → 9+8; Rwandan contexts (mangoes, cows)  |
| `subtraction`  | 4–8          | 12    | Take-away 10–1 → 20–13; basket/market context     |
| `word_problem` | 6–9          | 12    | RWF, water point, mandazi contexts                |

---

## Knowledge Tracing

`kt_eval.ipynb` evaluates three models on a 200-student synthetic replay:

| Model           | AUC (expected) |
| --------------- | -------------- |
| BKT             | 0.72–0.78      |
| GRU (hidden=32) | 0.74–0.80      |
| Elo baseline    | 0.65–0.70      |

---

## Footprint

The `tutor/` package (including ONNX models) targets ≤ 75 MB. TTS cache (`~/.cache/math-tutor-tts/`) is excluded from this limit.

```bash
du -sh tutor/
```

See [footprint_report.md](footprint_report.md) for a per-component breakdown.

---
