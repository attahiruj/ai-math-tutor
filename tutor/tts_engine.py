"""TTS Engine: Piper TTS (primary) → Coqui TTS (secondary) → pyttsx3 (last resort).

Challenge requirement: render TTS lines locally with Coqui-TTS or Piper TTS.
Cache to ~/.cache/math-tutor-tts/; cache is NOT counted in the 75 MB footprint.

Piper voices are downloaded on first use to ~/.cache/math-tutor-tts/piper-voices/.
Coqui TTS is used when `TTS` package is installed (pip install TTS).
pyttsx3 is a last-resort fallback when neither Piper binary nor Coqui are available.
"""

import hashlib
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

TTS_CACHE_DIR = Path.home() / ".cache" / "math-tutor-tts"
PIPER_VOICE_DIR = TTS_CACHE_DIR / "piper-voices"
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
PIPER_VOICE_DIR.mkdir(parents=True, exist_ok=True)

# Piper voice model names (ONNX files downloaded from Piper releases)
PIPER_VOICES = {
    "en": "en_US-lessac-medium",
    "fr": "fr_FR-siwis-medium",
    # No Kinyarwanda Piper voice exists; use English as proxy
    "kin": "en_US-lessac-medium",
}

# Coqui TTS model names (auto-downloaded by the TTS library)
COQUI_MODELS = {
    "en": "tts_models/en/ljspeech/tacotron2-DDC",
    "fr": "tts_models/fr/mai/tacotron2-DDC",
    "kin": "tts_models/en/ljspeech/tacotron2-DDC",  # proxy
}

PYTTSX3_LANG_RATES = {"en": 150, "fr": 145, "kin": 140}


# ── helpers ───────────────────────────────────────────────────────────────────

def _cache_key(text: str, lang: str) -> Path:
    h = hashlib.sha256((text + lang).encode()).hexdigest()[:16]
    return TTS_CACHE_DIR / (h + ".wav")


# ── Tier 1: Piper TTS (subprocess) ───────────────────────────────────────────

def _piper_binary() -> str | None:
    return shutil.which("piper") or shutil.which("piper-tts")


def _piper_voice_path(lang: str) -> Path | None:
    """Return path to the .onnx voice model, downloading it if needed."""
    voice_name = PIPER_VOICES.get(lang, PIPER_VOICES["en"])
    onnx = PIPER_VOICE_DIR / (voice_name + ".onnx")
    json = PIPER_VOICE_DIR / (voice_name + ".onnx.json")
    if onnx.exists() and json.exists():
        return onnx
    # Download from Piper releases (requires internet on first run)
    base_url = (
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        + voice_name.replace("-", "/", 1).replace("-", "/", 1)
        + "/"
        + voice_name
    )
    try:
        import urllib.request
        logger.info("Downloading Piper voice %s …", voice_name)
        urllib.request.urlretrieve(base_url + ".onnx", onnx)
        urllib.request.urlretrieve(base_url + ".onnx.json", json)
        return onnx
    except Exception as exc:
        logger.warning("Piper voice download failed: %s", exc)
        if onnx.exists():
            onnx.unlink(missing_ok=True)
        return None


def _speak_piper(text: str, lang: str, out_path: Path) -> bool:
    binary = _piper_binary()
    if binary is None:
        return False
    voice_path = _piper_voice_path(lang)
    if voice_path is None:
        return False
    try:
        result = subprocess.run(
            [binary, "--model", str(voice_path), "--output_file", str(out_path)],
            input=text.encode(),
            capture_output=True,
            timeout=15,
        )
        return result.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0
    except Exception as exc:
        logger.debug("Piper TTS failed: %s", exc)
        return False


# ── Tier 2: Coqui TTS (Python package) ───────────────────────────────────────

_coqui_instances: dict[str, object] = {}


def _speak_coqui(text: str, lang: str, out_path: Path) -> bool:
    try:
        from TTS.api import TTS as CoquiTTS  # type: ignore[import]
    except ImportError:
        return False
    try:
        if lang not in _coqui_instances:
            model = COQUI_MODELS.get(lang, COQUI_MODELS["en"])
            _coqui_instances[lang] = CoquiTTS(model_name=model, progress_bar=False, gpu=False)
        tts_instance = _coqui_instances[lang]
        tts_instance.tts_to_file(text=text, file_path=str(out_path))
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception as exc:
        logger.warning("Coqui TTS failed for lang=%s: %s", lang, exc)
        return False


# ── Tier 3: pyttsx3 (last resort) ────────────────────────────────────────────

def _speak_pyttsx3(text: str, lang: str, out_path: Path) -> bool:
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", PYTTSX3_LANG_RATES.get(lang, 150))
        voices = engine.getProperty("voices") or []
        lang_code = {"en": "en", "fr": "fr", "kin": "en"}.get(lang, "en")
        matched = next(
            (
                v for v in voices
                if lang_code in (v.languages[0] if v.languages else "").lower()
                or lang_code in v.id.lower()
            ),
            None,
        )
        if matched:
            engine.setProperty("voice", matched.id)
        engine.save_to_file(text, str(out_path))
        engine.runAndWait()
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception as exc:
        logger.warning("pyttsx3 TTS failed: %s", exc)
        return False


# ── Public API ────────────────────────────────────────────────────────────────

class TTSEngine:
    def speak(self, text: str, lang: str) -> bytes:
        cached = _cache_key(text, lang)
        if cached.exists() and cached.stat().st_size > 0:
            return cached.read_bytes()

        for backend in (_speak_piper, _speak_coqui, _speak_pyttsx3):
            if backend(text, lang, cached):
                return cached.read_bytes()
            # Remove partial file before next attempt
            cached.unlink(missing_ok=True)

        logger.error("All TTS backends failed for lang=%s text=%r", lang, text)
        return b""

    def prewarm(self, items: list[dict]) -> None:
        stem_keys = {"en": "stem_en", "fr": "stem_fr", "kin": "stem_kin"}
        new_files = 0
        for item in items:
            for lang, key in stem_keys.items():
                text = item.get(key) or item.get("stem_en", "")
                if not text:
                    continue
                cached = _cache_key(text, lang)
                if not cached.exists():
                    self.speak(text, lang)
                    new_files += 1
        logger.info("TTS prewarm complete: %d new files synthesised", new_files)
