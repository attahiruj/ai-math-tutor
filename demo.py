"""Gradio-based child-facing demo for AI Math Tutor.

Provides a simple interface for children to interact with the tutor via voice.
Requires the backend API running at http://localhost:8000.

Usage:
    gradio demo.py
    or
    python demo.py
"""

import os
import tempfile
import time

import gradio as gr
import requests

API = "http://localhost:8000"
TIMEOUT = 10  # seconds

_tmp_files: list[str] = []


def _fetch_audio(url: str) -> str | None:
    """Download audio from backend to a temp file; return path (avoids Gradio SSRF block)."""
    if not url:
        return None
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=".wav")
        with os.fdopen(fd, "wb") as f:
            f.write(r.content)
        _tmp_files.append(path)
        return path
    except Exception:
        return None


def _fetch_image(url: str) -> str | None:
    """Download image from backend to a temp file; return path."""
    if not url:
        return None
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=".png")
        with os.fdopen(fd, "wb") as f:
            f.write(r.content)
        _tmp_files.append(path)
        return path
    except Exception:
        return None


def start_session(name, lang):
    if not name.strip():
        return None, None, None, "Please enter your name.", gr.update(visible=False)
    try:
        r = requests.post(
            API + "/session/start",
            json={"name": name.strip(), "lang": lang, "icon": "star"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        return (
            data["student_id"],
            data["session_id"],
            lang,
            "Hello {}! Let's learn math!".format(name),
            gr.update(visible=True),
        )
    except Exception as e:
        return None, None, None, "Error: {}".format(e), gr.update(visible=False)


def get_next_item(student_id, session_id, lang):
    """Fetch the next item; returns 8 values (includes tap_btn visibility)."""
    _hidden = gr.update(visible=False)
    if not student_id:
        return None, "", None, None, "", _hidden, _hidden, _hidden

    try:
        r = requests.get(
            API + "/item/next",
            params={"student_id": student_id, "lang": lang},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        item = r.json()
        stem = item.get("stem_localized", "")
        item_id = item["id"]
        visual_url = item.get("visual_url", "")

        image_path = _fetch_image(API + visual_url) if visual_url else None
        tts_path = _fetch_audio(API + "/tts/" + lang + "/" + item_id)

        answer = item.get("answer_int")
        distractors = item.get("distractors", [])
        choices = sorted(dict.fromkeys([answer] + distractors))

        return (
            item_id,
            stem,
            image_path,
            tts_path,
            "Question ready! Tap or speak your answer.",
            gr.update(visible=True),                                          # voice_btn
            gr.update(visible=True, choices=[str(c) for c in choices], value=None),  # tap_radio
            gr.update(visible=True),                                          # tap_btn
        )
    except Exception as e:
        return None, "", None, None, "Error fetching item: {}".format(e), _hidden, _hidden, _hidden


def submit_voice(student_id, session_id, item_id, lang, audio):
    if not audio or not item_id:
        return "No audio recorded.", None, gr.update(value=None)
    try:
        with open(audio, "rb") as f:
            r = requests.post(
                API + "/answer/voice",
                data={"student_id": student_id, "session_id": session_id,
                      "item_id": item_id, "lang": lang},
                files={"audio": ("audio.wav", f, "audio/wav")},
                timeout=TIMEOUT,
            )
        r.raise_for_status()
        result = r.json()
        correct = result.get("correct", False)
        feedback = result.get("feedback_text", "")
        transcribed = result.get("transcribed", "")
        feedback_lang = result.get("detected_lang", lang)
        fb_url = (
            API + "/tts/" + feedback_lang + "/speak?text=" + requests.utils.quote(feedback)
        )
        return (
            ("Correct! " if correct else "Not quite. ") + feedback,
            _fetch_audio(fb_url),
            gr.update(value="Transcribed: {}".format(transcribed)),
        )
    except Exception as e:
        return "Error: {}".format(e), None, gr.update(value="")


def submit_tap(student_id, session_id, item_id, lang, choice):
    if choice is None or not item_id:
        return "Please select an answer.", None, gr.update(value="")
    try:
        r = requests.post(
            API + "/answer/tap",
            json={"student_id": student_id, "session_id": session_id,
                  "item_id": item_id, "choice": int(choice)},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        result = r.json()
        correct = result.get("correct", False)
        feedback = result.get("feedback_text", "")
        fb_url = API + "/tts/" + lang + "/speak?text=" + requests.utils.quote(feedback)
        return (
            ("Correct! " if correct else "Not quite. ") + feedback,
            _fetch_audio(fb_url),
            gr.update(value="You tapped: {}".format(choice)),
        )
    except Exception as e:
        return "Error: {}".format(e), None, gr.update(value="")


# ── Gradio UI ────────────────────────────────────────────────────────────────

with gr.Blocks(title="AI Math Tutor - Child Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI Math Tutor - Child Demo\nA voice-enabled math practice for kids.")

    student_id_s = gr.State(value=None)
    session_id_s = gr.State(value=None)
    lang_s = gr.State(value="en")
    current_item_id = gr.State(value=None)

    # ── Step 1: Start session ────────────────────────────────────────────────
    with gr.Group():
        gr.Markdown("### 1. Who are you?")
        with gr.Row():
            name_in = gr.Textbox(label="Your name", placeholder="Enter your name", scale=2)
            lang_in = gr.Dropdown(["en", "fr", "kin"], value="en", label="Language", scale=1)
        start_btn = gr.Button("Start!")
        start_msg = gr.Markdown("")

    # ── Step 2: Question area ────────────────────────────────────────────────
    with gr.Group(visible=False) as q_group:
        gr.Markdown("### 2. Question")
        stem_txt = gr.Markdown("")
        item_image = gr.Image(label="Look!", type="filepath", interactive=False)
        stem_audio = gr.Audio(label="Listen", autoplay=True, visible=False)
        q_status = gr.Markdown("")

        gr.Markdown("#### Tap your answer")
        tap_radio = gr.Radio(label="Choose one", choices=[], visible=False)
        tap_btn = gr.Button("Submit tap", visible=False)

        gr.Markdown("#### Or speak your answer")
        mic = gr.Audio(sources=["microphone"], type="filepath", label="Record your answer")
        voice_btn = gr.Button("Submit voice", visible=False)

    # ── Feedback area ────────────────────────────────────────────────────────
    with gr.Group():
        gr.Markdown("### Result")
        feedback_txt = gr.Markdown("")
        feedback_audio = gr.Audio(label="Feedback audio", autoplay=True, visible=False)
        details_md = gr.Markdown("")
        next_btn = gr.Button("Next question", visible=False)

    # ── Callbacks ────────────────────────────────────────────────────────────

    def on_start(name, lang):
        sid, sess, lg, msg, show_q = start_session(name, lang)
        if sid:
            item_id, stem, img, tts, status, v_btn, t_radio, t_btn = get_next_item(sid, sess, lg)
            return (
                sid, sess, lg, item_id, msg,
                gr.update(visible=True),                        # q_group
                stem,
                gr.update(value=img, visible=bool(img)),        # item_image
                gr.update(value=tts, visible=bool(tts)),        # stem_audio
                status, v_btn, t_radio, t_btn,
                "", gr.update(visible=False), "", gr.update(visible=False),  # clear result
            )
        return (
            None, None, lang, None, msg,
            gr.update(visible=False), "",
            gr.update(visible=False), gr.update(visible=False),
            "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            "", gr.update(visible=False), "", gr.update(visible=False),
        )

    start_btn.click(
        on_start,
        inputs=[name_in, lang_in],
        outputs=[
            student_id_s, session_id_s, lang_s, current_item_id, start_msg,
            q_group, stem_txt, item_image, stem_audio, q_status,
            voice_btn, tap_radio, tap_btn,
            feedback_txt, feedback_audio, details_md, next_btn,
        ],
    )

    def on_voice_submit(sid, sess, item_id, lang, audio):
        feedback, fb_path, details = submit_voice(sid, sess, item_id, lang, audio)
        return (
            feedback,
            gr.update(value=fb_path, visible=bool(fb_path)),
            details,
            gr.update(visible=True),   # next_btn
            gr.update(visible=False),  # hide voice_btn after submit
            gr.update(visible=False),  # hide tap_btn after submit
        )

    voice_btn.click(
        on_voice_submit,
        inputs=[student_id_s, session_id_s, current_item_id, lang_s, mic],
        outputs=[feedback_txt, feedback_audio, details_md, next_btn, voice_btn, tap_btn],
    )

    def on_tap_submit(sid, sess, item_id, lang, choice):
        feedback, fb_path, details = submit_tap(sid, sess, item_id, lang, choice)
        return (
            feedback,
            gr.update(value=fb_path, visible=bool(fb_path)),
            details,
            gr.update(visible=True),   # next_btn
            gr.update(visible=False),  # hide tap_btn after submit
            gr.update(visible=False),  # hide voice_btn after submit
        )

    tap_btn.click(
        on_tap_submit,
        inputs=[student_id_s, session_id_s, current_item_id, lang_s, tap_radio],
        outputs=[feedback_txt, feedback_audio, details_md, next_btn, tap_btn, voice_btn],
    )

    def on_next(sid, sess, lang):
        _h = gr.update(visible=False)
        if not sid:
            return (None, "", _h, _h, "", _h, _h, _h, "", _h, "", _h, gr.update(value=None))
        item_id, stem, img, tts, status, v_btn, t_radio, t_btn = get_next_item(sid, sess, lang)
        return (
            item_id, stem,
            gr.update(value=img, visible=bool(img)),
            gr.update(value=tts, visible=bool(tts)),
            status, v_btn, t_radio, t_btn,
            "", _h, "", _h,           # clear feedback + hide next_btn
            gr.update(value=None),    # clear mic
        )

    next_btn.click(
        on_next,
        inputs=[student_id_s, session_id_s, lang_s],
        outputs=[
            current_item_id, stem_txt, item_image, stem_audio, q_status,
            voice_btn, tap_radio, tap_btn,
            feedback_txt, feedback_audio, details_md, next_btn,
            mic,
        ],
    )


if __name__ == "__main__":
    demo.launch(share=False, server_port=7860)
