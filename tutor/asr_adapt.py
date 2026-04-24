"""ASR module: Whisper-tiny INT8 ONNX transcriber with child-voice adaptation."""

import re
from pathlib import Path

import numpy as np

MODEL_DIR = Path("tutor/models/whisper-tiny-fp32")
ENCODER_PATH = Path("tutor/models/whisper-tiny-int8.onnx")
DECODER_PATH = Path("tutor/models/whisper-tiny-decoder-int8.onnx")

# Whisper special tokens
_SOT = 50258
_EOT = 50257
_TRANSCRIBE = 50359
_NO_TS = 50363

# Language tokens (from generation_config.json; kin not in whisper-tiny -> en)
_LANG_TOKEN = {"en": 50259, "fr": 50265, "kin": 50259}

_KIN_NUMBERS = {
    "rimwe": 1, "kabiri": 2, "gatatu": 3, "kane": 4, "gatanu": 5,
    "gatandatu": 6, "indwi": 7, "umunani": 8, "icyenda": 9, "icumi": 10,
    "makumyabiri": 20,
}
_FR_NUMBERS = {
    "zero": 0, "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4,
    "cinq": 5, "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10,
    "onze": 11, "douze": 12, "treize": 13, "quatorze": 14, "quinze": 15,
    "seize": 16, "dix-sept": 17, "dix-huit": 18, "dix-neuf": 19, "vingt": 20,
}
_EN_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}
_ALL_WORD_NUMS = {**_KIN_NUMBERS, **_FR_NUMBERS, **_EN_NUMBERS}

# Whisper mel spectrogram constants
_SR = 16000
_N_FFT = 400
_HOP = 160
_N_MELS = 80
_FRAMES = 3000  # 30 s of audio at 10ms hop


def _log_mel(audio: np.ndarray) -> np.ndarray:
    """Compute Whisper-compatible log-mel spectrogram [1, 80, 3000]."""
    import librosa

    # Pad / truncate to exactly 30 s
    target = _SR * 30
    if len(audio) < target:
        audio = np.pad(audio, (0, target - len(audio)))
    else:
        audio = audio[:target]

    mel = librosa.feature.melspectrogram(
        y=audio,
        sr=_SR,
        n_fft=_N_FFT,
        hop_length=_HOP,
        n_mels=_N_MELS,
        fmin=0.0,
        fmax=8000.0,
        center=True,
        pad_mode="reflect",
    )
    # Whisper normalization
    log_mel = np.log10(np.maximum(mel, 1e-10))
    log_mel = np.maximum(log_mel, log_mel.max() - 8.0)
    log_mel = (log_mel + 4.0) / 4.0

    # Ensure exactly 3000 frames
    if log_mel.shape[1] < _FRAMES:
        log_mel = np.pad(log_mel, ((0, 0), (0, _FRAMES - log_mel.shape[1])))
    else:
        log_mel = log_mel[:, :_FRAMES]

    return log_mel[np.newaxis].astype(np.float32)  # [1, 80, 3000]


def _trim_silence(audio: np.ndarray, rms_threshold: float = 0.01) -> np.ndarray:
    frame = 512
    rms = np.array([
        np.sqrt(np.mean(audio[i : i + frame] ** 2))
        for i in range(0, len(audio), frame)
    ])
    active = np.where(rms > rms_threshold)[0]
    if len(active) == 0:
        return audio
    start = active[0] * frame
    end = min((active[-1] + 1) * frame, len(audio))
    return audio[start:end]


class WhisperONNXTranscriber:
    def __init__(
        self,
        model_path: str = str(ENCODER_PATH),
        decoder_path: str = str(DECODER_PATH),
    ):
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 2
        opts.intra_op_num_threads = 2

        self._enc = ort.InferenceSession(model_path, sess_options=opts)
        self._dec = ort.InferenceSession(decoder_path, sess_options=opts)
        self._tok = None  # lazy-loaded on first transcribe

    def _get_tokenizer(self):
        if self._tok is None:
            from transformers import WhisperTokenizer
            self._tok = WhisperTokenizer.from_pretrained(str(MODEL_DIR))
        return self._tok

    def transcribe(
        self,
        audio_np: np.ndarray,
        sample_rate: int,
        lang_hint: str | None = None,
    ) -> str:
        audio = self._preprocess(audio_np, sample_rate)
        mel = _log_mel(audio)
        enc_out = self._enc.run(None, {"input_features": mel})[0]  # [1, 1500, 384]
        tokens = self._decode(enc_out, lang_hint or "en")
        tok = self._get_tokenizer()
        text = tok.decode(tokens, skip_special_tokens=True).strip().lower()
        return text

    def _preprocess(self, audio: np.ndarray, sr: int) -> np.ndarray:
        import librosa

        audio = audio.astype(np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=-1)
        if sr != _SR:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=_SR)
        # Child-voice adaptation: children speak ~4 semitones above adult pitch.
        # Shift DOWN by 4 st so Whisper (trained on adults) transcribes correctly.
        audio = librosa.effects.pitch_shift(audio, sr=_SR, n_steps=-4)
        return _trim_silence(audio)

    def _decode(self, enc_hidden: np.ndarray, lang: str, max_new_tokens: int = 30) -> list[int]:
        lang_tok = _LANG_TOKEN.get(lang, _LANG_TOKEN["en"])
        forced = [_SOT, lang_tok, _TRANSCRIBE, _NO_TS]
        input_ids = list(forced)

        for _ in range(max_new_tokens):
            ids_arr = np.array([input_ids], dtype=np.int64)
            logits = self._dec.run(
                ["logits"],
                {"input_ids": ids_arr, "encoder_hidden_states": enc_hidden},
            )[0]  # [1, seq_len, 51865]
            next_tok = int(np.argmax(logits[0, -1]))
            if next_tok == _EOT:
                break
            input_ids.append(next_tok)

        return input_ids[len(forced):]


def extract_number(text: str, lang: str = "en") -> int | None:
    """Return integer from transcribed text: digit patterns first, then word maps."""
    text = text.strip().lower()

    m = re.search(r"\b(\d+)\b", text)
    if m:
        return int(m.group(1))

    lookup = {"kin": _KIN_NUMBERS, "fr": _FR_NUMBERS, "en": _EN_NUMBERS}.get(lang, _ALL_WORD_NUMS)
    for word, val in lookup.items():
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            return val

    for word, val in _ALL_WORD_NUMS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            return val

    return None


def score_response(item: dict, transcribed: str) -> bool:
    """True if transcribed text matches item answer (numeric extraction or fuzzy)."""
    from Levenshtein import distance as lev_dist

    answer = item["answer_int"]
    text = transcribed.strip().lower()

    extracted = extract_number(text)
    if extracted is not None and extracted == answer:
        return True

    if lev_dist(text, str(answer)) <= 1:
        return True

    return False
