"""parent_report.py — Generate JSON and HTML parent-facing progress reports."""

import base64
import datetime
import io

import qrcode

from tutor.adaptive import SKILL_PARAMS

SKILL_ICONS = {
    "counting": "🔢",
    "number_sense": "🧮",
    "addition": "➕",
    "subtraction": "➖",
    "word_problem": "📖",
}

ALL_SKILLS = ["counting", "number_sense", "addition", "subtraction", "word_problem"]


def build_report_json(student_id: str, summary: dict, bkt_state: dict) -> dict:
    """Transform DB summary into res/parent_report_schema.json format."""
    week_start = (datetime.date.today() - datetime.timedelta(days=6)).isoformat()
    sessions = sum(1 for d in summary.get("daily_attendance", []) if d.get("total", 0) > 0)

    skills_out = {}
    for skill in ALL_SKILLS:
        current = round(bkt_state.get(skill, {}).get("p_mastery", SKILL_PARAMS[skill]["p_init"]), 3)
        p_init = SKILL_PARAMS[skill]["p_init"]
        skills_out[skill] = {"current": current, "delta": round(current - p_init, 3)}

    overall = summary.get("overall_accuracy", 0.0)
    overall_arrow = "↑" if overall >= 0.7 else "→" if overall >= 0.4 else "↓"
    best = max(ALL_SKILLS, key=lambda s: skills_out[s]["current"])
    needs_help = min(ALL_SKILLS, key=lambda s: skills_out[s]["current"])

    return {
        "learner_id": student_id,
        "week_starting": week_start,
        "sessions": sessions,
        "skills": skills_out,
        "icons_for_parent": [overall_arrow, SKILL_ICONS[best], SKILL_ICONS[needs_help]],
        "voiced_summary_audio": f"data/tts/report_{student_id}.wav",
    }


def build_voiced_text(student_name: str, report: dict, lang: str = "en") -> str:
    """Return a TTS-friendly one-sentence summary in the requested language."""
    icons = report["icons_for_parent"]
    overall_arrow = icons[0]
    best = next((k for k in ALL_SKILLS if SKILL_ICONS[k] == icons[1]), ALL_SKILLS[0])
    help_skill = next((k for k in ALL_SKILLS if SKILL_ICONS[k] == icons[2]), ALL_SKILLS[-1])
    best_nice = best.replace("_", " ")
    help_nice = help_skill.replace("_", " ")

    trend = {
        "en": {"↑": "improving", "→": "steady", "↓": "needs more practice"},
        "fr": {"↑": "en progrès", "→": "stable", "↓": "besoin de pratique"},
        "kin": {"↑": "ariyongera", "→": "arikomeje", "↓": "akeneye gutsinda"},
    }.get(lang, {}).get(overall_arrow, "steady")

    if lang == "fr":
        return (
            f"{student_name} est {trend} en mathématiques cette semaine. "
            f"Meilleure compétence: {best_nice}. "
            f"À travailler: {help_nice}."
        )
    if lang == "kin":
        return (
            f"{student_name} {trend} muri matematike. "
            f"Ubuhanga bwiza: {best_nice}. "
            f"Gukomezaho: {help_nice}."
        )
    return (
        f"{student_name} is {trend} in math this week. "
        f"Best skill: {best_nice}. "
        f"Needs more work on: {help_nice}."
    )


def build_qr_png(student_id: str, base_url: str = "http://localhost:8000") -> bytes:
    """Return QR code PNG bytes pointing to the voiced report endpoint."""
    url = f"{base_url}/report/{student_id}/voiced"
    qr = qrcode.QRCode(version=1, box_size=6, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def build_report_html(student: dict, summary: dict, report: dict) -> str:
    """Build parent-facing HTML with skills, attendance dots, smiley, and QR code."""
    name = student["name"]
    skills = report["skills"]
    icons = report["icons_for_parent"]
    overall_arrow = icons[0]
    smiley = "😊" if overall_arrow == "↑" else "🙂" if overall_arrow == "→" else "😐"
    overall_pct = int(summary.get("overall_accuracy", 0.0) * 100)
    week_start = report["week_starting"]
    sessions = report["sessions"]
    total_attempts = summary.get("total_attempts", 0)

    # ── Skill rows ──
    skill_rows_html = ""
    for skill in ALL_SKILLS:
        data = skills.get(skill, {"current": 0.0, "delta": 0.0})
        pct = int(data["current"] * 100)
        delta = data["delta"]
        color = "#4CAF50" if pct >= 70 else "#FFC107" if pct >= 40 else "#90CAF9"
        filled = round(data["current"] * 5)
        stars = "★" * filled + "☆" * (5 - filled)
        delta_sign = "+" if delta >= 0 else ""
        delta_str = f"{delta_sign}{delta:.0%}"
        delta_color = "#4CAF50" if delta >= 0 else "#F44336"
        icon = SKILL_ICONS[skill]
        skill_rows_html += f"""
      <div class="skill-row">
        <span class="icon">{icon}</span>
        <span class="name">{skill.replace('_', ' ').title()}</span>
        <span class="stars">{stars}</span>
        <div class="bar-bg"><div class="bar" style="width:{pct}%;background:{color}"></div></div>
        <span class="pct">{pct}%</span>
        <span class="delta" style="color:{delta_color}">{delta_str}</span>
      </div>"""

    # ── Attendance dots ──
    att_dots = "".join(
        f'<span class="dot" title="Day {i + 1}">{"●" if d.get("total", 0) > 0 else "○"}</span>'
        for i, d in enumerate(summary.get("daily_attendance", []))
    )

    # ── QR code (base64-embedded) ──
    try:
        qr_bytes = build_qr_png(student["id"])
        qr_b64 = base64.b64encode(qr_bytes).decode()
        qr_tag = (
            f'<img src="data:image/png;base64,{qr_b64}" '
            f'alt="QR Code" style="width:120px;height:120px">'
        )
    except Exception:
        qr_tag = "<p style='font-size:.8rem;color:#888'>QR unavailable</p>"

    session_label = "session" if sessions == 1 else "sessions"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Weekly Report — {name}</title>
  <style>
    body {{font-family:sans-serif;max-width:520px;margin:auto;padding:16px;background:#f5f5f5;color:#333}}
    h1 {{font-size:1.4rem;text-align:center;margin-bottom:4px}}
    .sub {{text-align:center;font-size:.85rem;color:#777;margin-bottom:16px}}
    .card {{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.10);padding:16px;margin-bottom:12px}}
    .skill-row {{display:flex;align-items:center;gap:6px;margin:8px 0}}
    .icon {{font-size:1.2rem;width:28px;text-align:center}}
    .name {{flex:1;font-size:.88rem}}
    .stars {{color:#f5a623;font-size:.88rem;white-space:nowrap}}
    .bar-bg {{flex:2;background:#e0e0e0;border-radius:6px;height:10px;overflow:hidden}}
    .bar {{height:10px;border-radius:6px}}
    .pct {{font-size:.8rem;color:#555;width:30px;text-align:right}}
    .delta {{font-size:.75rem;width:36px;text-align:right;white-space:nowrap}}
    .dots {{font-size:1.6rem;letter-spacing:5px;margin:4px 0}}
    .summary-banner {{display:flex;align-items:center;justify-content:center;gap:12px;font-size:2rem;padding:8px 0}}
    .summary-text {{font-size:.95rem;text-align:center;color:#555;margin:4px 0}}
    .qr-section {{display:flex;flex-direction:column;align-items:center;gap:6px}}
    .qr-caption {{font-size:.75rem;color:#888;text-align:center}}
    h3 {{margin:0 0 10px;font-size:.95rem;color:#555}}
    .stat {{font-size:.85rem;color:#666;margin-top:6px}}
  </style>
</head>
<body>
  <h1>📊 Weekly Report</h1>
  <p class="sub">{name} &middot; Week of {week_start} &middot; {sessions} {session_label}</p>

  <div class="card">
    <h3>Skill Progress</h3>
    {skill_rows_html}
  </div>

  <div class="card">
    <h3>Attendance (last 7 days)</h3>
    <div class="dots">{att_dots}</div>
    <p class="stat">Total attempts this week: {total_attempts}</p>
  </div>

  <div class="card">
    <div class="summary-banner">{smiley} {overall_arrow}</div>
    <p class="summary-text">Overall accuracy: <strong>{overall_pct}%</strong></p>
    <p class="summary-text">Best: {icons[1]} &nbsp;|&nbsp; Focus: {icons[2]}</p>
  </div>

  <div class="card qr-section">
    <h3 style="text-align:center">Share voiced report</h3>
    {qr_tag}
    <p class="qr-caption">Scan to hear an audio summary of {name}'s progress</p>
  </div>
</body>
</html>"""
