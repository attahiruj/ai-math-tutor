# Footprint Report — AI Math Tutor

Generated: 2026-04-24

## Directory Sizes

| Directory     | Size (MB)                  |
| ------------- | -------------------------- |
| tutor/        | 0.0*                       |
| tutor/models/ | (model not yet downloaded) |
| frontend/     | (static files)             |
| data/         | (runtime data)             |
| .venv/        | (excluded from footprint)  |

*The tutor/ directory is empty of model files (no .onnx yet). After downloading whisper-tiny-int8.onnx, the footprint should be ≤ 75 MB.

## Model Download

To download and quantize the Whisper-tiny model:

```bash
cd "C:\Users\attah\dev\aims_ktt\day_03\ai-math-tutor"
.venv\Scripts\python.exe scripts\download_model.py
```

Expected model size: ~40-45 MB (INT8 quantized)

## Notes

- The whisper-tiny-int8.onnx model is NOT included in the repository (added to .gitignore)
- Data files (curriculum_full.json, images/, tts/) are generated at runtime or excluded from version control
- Frontend is served statically; no build step required
