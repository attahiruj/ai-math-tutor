"""
Download and quantize Whisper-tiny to INT8 ONNX for the AI Math Tutor.

Usage:
    uv run python scripts/download_model.py

Output:
    tutor/models/whisper-tiny-int8.onnx
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

FP32_DIR = Path("tutor/models/whisper-tiny-fp32")
INT8_PATH = Path("tutor/models/whisper-tiny-int8.onnx")
ENCODER_FP32 = FP32_DIR / "encoder_model.onnx"
DECODER_FP32 = FP32_DIR / "decoder_model.onnx"


def export_from_hf():
    print("Exporting whisper-tiny from HuggingFace via optimum-cli...")
    FP32_DIR.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable, "-m", "optimum.exporters.onnx",
            "--model", "openai/whisper-tiny",
            "--task", "automatic-speech-recognition",
            str(FP32_DIR),
        ],
        capture_output=False,
    )
    if result.returncode != 0:
        raise RuntimeError("optimum export failed - see output above")
    print(f"Export complete: {FP32_DIR}")


def quantize_to_int8():
    from onnxruntime.quantization import quantize_dynamic, QuantType

    # Optimum exports separate encoder/decoder - quantize both and pick larger
    # For inference we only need the combined model_fp32; try common names.
    candidates = list(FP32_DIR.glob("*.onnx"))
    if not candidates:
        raise FileNotFoundError(f"No .onnx files found in {FP32_DIR}")

    print(f"Found ONNX files: {[c.name for c in candidates]}")

    # Quantize each file; the main model is typically model.onnx or encoder_model.onnx
    output_files = []
    for src in candidates:
        dst = FP32_DIR / f"{src.stem}_int8.onnx"
        print(f"Quantizing {src.name} -> {dst.name} ...")
        quantize_dynamic(str(src), str(dst), weight_type=QuantType.QInt8)
        size_mb = dst.stat().st_size / (1024 ** 2)
        print(f"  {dst.name}: {size_mb:.1f} MB")
        output_files.append((dst, size_mb))

    # Copy encoder (largest) and decoder to predictable paths for asr_adapt.py
    largest = max(output_files, key=lambda x: x[1])
    shutil.copy2(largest[0], INT8_PATH)
    print(f"\nEncoder (primary) -> {INT8_PATH} ({largest[1]:.1f} MB)")

    decoder_int8 = next(
        (p for p, _ in output_files if "decoder" in p.stem.lower()), None
    )
    if decoder_int8:
        decoder_dst = INT8_PATH.parent / "whisper-tiny-decoder-int8.onnx"
        shutil.copy2(decoder_int8, decoder_dst)
        print(f"Decoder -> {decoder_dst} ({decoder_dst.stat().st_size / (1024**2):.1f} MB)")


def verify():
    if not INT8_PATH.exists():
        print("FAIL: INT8 model not found")
        return False
    size_mb = INT8_PATH.stat().st_size / (1024 ** 2)
    print(f"\nVerification: {INT8_PATH} = {size_mb:.1f} MB")
    if size_mb > 50:
        print(f"WARNING: model is {size_mb:.1f} MB - exceeds 50 MB target")
        return False
    print("OK: footprint within 50 MB limit")
    return True


def main():
    if INT8_PATH.exists():
        size_mb = INT8_PATH.stat().st_size / (1024 ** 2)
        print(f"INT8 model already exists ({size_mb:.1f} MB). Delete to re-download.")
        verify()
        return

    try:
        if not any(FP32_DIR.glob("*.onnx")):
            export_from_hf()
        else:
            print(f"FP32 models already present in {FP32_DIR}, skipping export.")
        quantize_to_int8()
        verify()
    except Exception as exc:
        print(f"\nExport/quantize failed: {exc}")
        print("Falling back to pre-quantized model from onnx-community/whisper-tiny ...")
        fallback()


def fallback():
    """Download pre-quantized ONNX files from onnx-community/whisper-tiny via huggingface_hub."""
    from huggingface_hub import hf_hub_download

    FP32_DIR.mkdir(parents=True, exist_ok=True)

    # onnx-community/whisper-tiny ships separate encoder + decoder int8 files.
    # We download both; the ASR module will use them individually.
    files_to_fetch = [
        "onnx/encoder_model_int8.onnx",
        "onnx/decoder_model_int8.onnx",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
        "merges.txt",
        "normalizer.json",
        "special_tokens_map.json",
        "preprocessor_config.json",
        "config.json",
        "generation_config.json",
    ]

    for filename in files_to_fetch:
        dest = FP32_DIR / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            print(f"  Downloading {filename} ...")
            local = hf_hub_download(
                repo_id="onnx-community/whisper-tiny",
                filename=filename,
                local_dir=str(FP32_DIR),
            )
            print(f"    -> {local}")
        except Exception as e:
            print(f"    WARNING: could not fetch {filename}: {e}")

    # Find the encoder int8 as the primary model (largest single-file representation)
    candidates = sorted(FP32_DIR.rglob("*.onnx"), key=lambda p: p.stat().st_size, reverse=True)
    if not candidates:
        raise FileNotFoundError("No ONNX files found after fallback download")

    int8_candidates = [p for p in candidates if "int8" in p.name.lower()]
    encoder = next((p for p in int8_candidates if "encoder" in p.name.lower()), None)
    decoder = next((p for p in int8_candidates if "decoder" in p.name.lower()), None)

    # Primary model path used by asr_adapt.py (encoder)
    chosen = encoder or (int8_candidates[0] if int8_candidates else candidates[0])
    shutil.copy2(chosen, INT8_PATH)

    # Also expose decoder at a predictable path for ASR module
    if decoder:
        decoder_dst = INT8_PATH.parent / "whisper-tiny-decoder-int8.onnx"
        shutil.copy2(decoder, decoder_dst)
        print(f"Decoder -> {decoder_dst} ({decoder.stat().st_size / (1024**2):.1f} MB)")

    size_mb = INT8_PATH.stat().st_size / (1024 ** 2)
    print(f"\nEncoder (primary) -> {INT8_PATH} ({size_mb:.1f} MB)")
    verify()


if __name__ == "__main__":
    main()
