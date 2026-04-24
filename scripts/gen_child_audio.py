"""Generate child-voiced utterances for ASR evaluation.

Challenge requirement:
  "Generate child-voiced utterances by pitch-shifting the Common Voice +
   DigitalUmuganda subsets (+3 to +6 semitones) and applying classroom-noise
   overlay from MUSAN (https://www.openslr.org/17/)."

This script:
  1. Reads source WAV files from --input-dir (Common Voice / DigitalUmuganda clips).
  2. Pitch-shifts each clip by +3 to +6 semitones (randomly sampled per file)
     to simulate a child's voice register.
  3. Overlays classroom noise from a MUSAN noise file at a random SNR of 10–20 dB.
  4. Writes augmented WAVs to --output-dir.

Usage:
  # Download MUSAN noise subset first:
  #   wget https://www.openslr.org/resources/17/musan.tar.gz && tar -xzf musan.tar.gz
  uv run python scripts/gen_child_audio.py \\
      --input-dir data/common_voice_clips/ \\
      --output-dir data/child_audio/ \\
      --musan-dir musan/noise/free-sound/ \\
      --count 200
"""

import argparse
import random
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

SR = 16_000
PITCH_SHIFT_MIN = 3  # semitones
PITCH_SHIFT_MAX = 6
SNR_MIN_DB = 10.0
SNR_MAX_DB = 20.0


def load_audio(path: Path) -> np.ndarray:
    audio, sr = librosa.load(path, sr=SR, mono=True)
    return audio.astype(np.float32)


def pitch_shift_childlike(audio: np.ndarray, n_steps: float) -> np.ndarray:
    """Shift pitch up by n_steps semitones to simulate a child's higher voice."""
    return librosa.effects.pitch_shift(audio, sr=SR, n_steps=n_steps)


def overlay_noise(speech: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    """Mix speech with noise at the given SNR (dB)."""
    # Tile noise to match speech length
    if len(noise) < len(speech):
        reps = int(np.ceil(len(speech) / len(noise)))
        noise = np.tile(noise, reps)
    noise = noise[: len(speech)]

    speech_rms = np.sqrt(np.mean(speech ** 2)) + 1e-9
    noise_rms = np.sqrt(np.mean(noise ** 2)) + 1e-9
    target_noise_rms = speech_rms / (10 ** (snr_db / 20))
    scaled_noise = noise * (target_noise_rms / noise_rms)

    mixed = speech + scaled_noise
    # Normalise to prevent clipping
    peak = np.max(np.abs(mixed))
    if peak > 0.99:
        mixed = mixed / peak * 0.99
    return mixed


def collect_files(directory: Path, extensions=(".wav", ".mp3", ".flac")) -> list[Path]:
    return [p for p in directory.rglob("*") if p.suffix.lower() in extensions]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate child-voiced audio for ASR evaluation")
    parser.add_argument("--input-dir", required=True, type=Path,
                        help="Directory of source adult speech WAV files")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="Directory to write augmented child-voiced WAVs")
    parser.add_argument("--musan-dir", type=Path, default=None,
                        help="MUSAN noise directory (musan/noise/). Skipped if absent.")
    parser.add_argument("--count", type=int, default=200,
                        help="Max number of output files to generate")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    source_files = collect_files(args.input_dir)
    if not source_files:
        raise SystemExit(f"No audio files found in {args.input_dir}")

    noise_files: list[Path] = []
    if args.musan_dir and args.musan_dir.exists():
        noise_files = collect_files(args.musan_dir)
        print(f"Found {len(noise_files)} MUSAN noise files")
    else:
        print("MUSAN dir not provided or not found — generating without noise overlay")

    random.shuffle(source_files)
    selected = source_files[: args.count]

    for i, src in enumerate(selected):
        try:
            speech = load_audio(src)
        except Exception as exc:
            print(f"  skip {src.name}: {exc}")
            continue

        # Random pitch shift in [+3, +6] semitones
        n_steps = random.uniform(PITCH_SHIFT_MIN, PITCH_SHIFT_MAX)
        child_speech = pitch_shift_childlike(speech, n_steps)

        # Optional classroom noise overlay
        if noise_files:
            noise_path = random.choice(noise_files)
            try:
                noise = load_audio(noise_path)
                snr = random.uniform(SNR_MIN_DB, SNR_MAX_DB)
                child_speech = overlay_noise(child_speech, noise, snr)
            except Exception as exc:
                print(f"  noise overlay failed ({noise_path.name}): {exc}")

        out_path = args.output_dir / (src.stem + f"_child_{i:04d}.wav")
        sf.write(out_path, child_speech, SR, subtype="PCM_16")

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(selected)} done")

    print(f"\nWrote {len(selected)} child-voiced WAVs to {args.output_dir}")


if __name__ == "__main__":
    main()
