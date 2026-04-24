import os
import sqlite3
import tempfile
import time
import uuid
import random
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

_APP_SALT = b"math-tutor-ai"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY, name TEXT, lang_pref TEXT, icon TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT, item_id TEXT, skill TEXT, difficulty INTEGER,
    correct INTEGER, response_time_ms INTEGER, lang_detected TEXT,
    response_method TEXT, timestamp REAL
);
CREATE TABLE IF NOT EXISTS bkt_state (
    student_id TEXT, skill TEXT, p_mastery REAL,
    attempts INTEGER, updated_at REAL,
    PRIMARY KEY (student_id, skill)
);
CREATE TABLE IF NOT EXISTS elo_state (
    student_id TEXT, skill TEXT, rating REAL, updated_at REAL,
    PRIMARY KEY (student_id, skill)
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT, start_time REAL, end_time REAL,
    item_count INTEGER, correct_count INTEGER
);
"""


def _derive_key(device_uuid: str) -> bytes:
    material = (device_uuid + _APP_SALT.decode()).encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_APP_SALT,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(material))


def _get_device_uuid() -> str:
    marker = os.path.join(os.path.expanduser("~"), ".math_tutor_uuid")
    if os.path.exists(marker):
        with open(marker) as f:
            return f.read().strip()
    uid = str(uuid.uuid4())
    with open(marker, "w") as f:
        f.write(uid)
    return uid


class ProgressDB:
    def __init__(self, enc_path: str = "data/progress.db.enc"):
        self._enc_path = enc_path
        self._key = _derive_key(_get_device_uuid())
        self._fernet = Fernet(self._key)
        self._tmp_path = None
        self._conn = None
        self._open()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _open(self):
        fd, tmp_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self._tmp_path = tmp_path

        if os.path.exists(self._enc_path) and os.path.getsize(self._enc_path) > 0:
            with open(self._enc_path, "rb") as f:
                ciphertext = f.read()
            plaintext = self._fernet.decrypt(ciphertext)
            with open(tmp_path, "wb") as f:
                f.write(plaintext)

        self._conn = sqlite3.connect(tmp_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self):
        if self._conn is None:
            return
        self._conn.commit()
        self._conn.close()
        enc_dir = os.path.dirname(self._enc_path)
        if enc_dir:
            os.makedirs(enc_dir, exist_ok=True)
        with open(self._tmp_path, "rb") as f:
            plaintext = f.read()
        ciphertext = self._fernet.encrypt(plaintext)
        with open(self._enc_path, "wb") as f:
            f.write(ciphertext)
        os.unlink(self._tmp_path)
        self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # Students
    # ------------------------------------------------------------------

    def create_student(self, name: str, lang_pref: str = "en", icon: str = "star") -> str:
        sid = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO students VALUES (?,?,?,?,?)",
            (sid, name, lang_pref, icon, time.time()),
        )
        self._conn.commit()
        return sid

    def get_student(self, student_id: str):
        row = self._conn.execute(
            "SELECT * FROM students WHERE id=?", (student_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_students(self) -> list:
        rows = self._conn.execute("SELECT * FROM students ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def start_session(self, student_id: str) -> int:
        cur = self._conn.execute(
            "INSERT INTO sessions (student_id, start_time, end_time, item_count, correct_count) "
            "VALUES (?,?,?,?,?)",
            (student_id, time.time(), None, 0, 0),
        )
        self._conn.commit()
        return cur.lastrowid

    def end_session(self, session_id: int) -> dict:
        row = self._conn.execute(
            "SELECT item_count, correct_count FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        self._conn.execute(
            "UPDATE sessions SET end_time=? WHERE id=?", (time.time(), session_id)
        )
        self._conn.commit()
        return dict(row) if row else {}

    # ------------------------------------------------------------------
    # Attempts
    # ------------------------------------------------------------------

    def record_attempt(
        self,
        student_id: str,
        item_id: str,
        skill: str,
        difficulty: int,
        correct: bool,
        response_time_ms: int,
        lang_detected: str = "en",
        method: str = "tap",
        session_id: int = None,
    ):
        self._conn.execute(
            "INSERT INTO attempts "
            "(student_id,item_id,skill,difficulty,correct,response_time_ms,"
            "lang_detected,response_method,timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                student_id, item_id, skill, difficulty,
                int(correct), response_time_ms,
                lang_detected, method, time.time(),
            ),
        )
        if session_id is not None:
            self._conn.execute(
                "UPDATE sessions SET item_count=item_count+1, correct_count=correct_count+? WHERE id=?",
                (int(correct), session_id),
            )
        self._conn.commit()

    # ------------------------------------------------------------------
    # BKT / Elo state
    # ------------------------------------------------------------------

    def save_bkt_state(self, student_id: str, skill: str, p_mastery: float, attempts: int):
        self._conn.execute(
            "INSERT OR REPLACE INTO bkt_state VALUES (?,?,?,?,?)",
            (student_id, skill, p_mastery, attempts, time.time()),
        )
        self._conn.commit()

    def load_bkt_state(self, student_id: str) -> dict:
        rows = self._conn.execute(
            "SELECT skill, p_mastery, attempts FROM bkt_state WHERE student_id=?",
            (student_id,),
        ).fetchall()
        return {r["skill"]: {"p_mastery": r["p_mastery"], "attempts": r["attempts"]} for r in rows}

    def save_elo_state(self, student_id: str, skill: str, rating: float):
        self._conn.execute(
            "INSERT OR REPLACE INTO elo_state VALUES (?,?,?,?)",
            (student_id, skill, rating, time.time()),
        )
        self._conn.commit()

    def load_elo_state(self, student_id: str) -> dict:
        rows = self._conn.execute(
            "SELECT skill, rating FROM elo_state WHERE student_id=?", (student_id,)
        ).fetchall()
        return {r["skill"]: r["rating"] for r in rows}

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def get_week_summary(self, student_id: str) -> dict:
        week_ago = time.time() - 7 * 86400
        rows = self._conn.execute(
            "SELECT skill, correct, difficulty, timestamp FROM attempts "
            "WHERE student_id=? AND timestamp>=?",
            (student_id, week_ago),
        ).fetchall()

        skill_stats = {}
        daily = {}

        for r in rows:
            s = r["skill"]
            if s not in skill_stats:
                skill_stats[s] = {"total": 0, "correct": 0}
            skill_stats[s]["total"] += 1
            skill_stats[s]["correct"] += r["correct"]

            day_offset = int((time.time() - r["timestamp"]) // 86400)
            day_key = 6 - day_offset
            if 0 <= day_key <= 6:
                if day_key not in daily:
                    daily[day_key] = {"total": 0, "correct": 0}
                daily[day_key]["total"] += 1
                daily[day_key]["correct"] += r["correct"]

        bkt = self.load_bkt_state(student_id)

        skill_summaries = []
        for skill, stats in skill_stats.items():
            accuracy = stats["correct"] / stats["total"] if stats["total"] else 0
            skill_summaries.append({
                "skill": skill,
                "accuracy": round(accuracy, 3),
                "attempts": stats["total"],
                "p_mastery": bkt.get(skill, {}).get("p_mastery", 0),
            })

        attendance = [{"day": i, **daily.get(i, {"total": 0, "correct": 0})} for i in range(7)]

        total_attempts = sum(s["attempts"] for s in skill_summaries)
        overall_accuracy = (
            sum(s["accuracy"] * s["attempts"] for s in skill_summaries) / max(total_attempts, 1)
        )

        return {
            "student_id": student_id,
            "period_days": 7,
            "skills": skill_summaries,
            "daily_attendance": attendance,
            "total_attempts": total_attempts,
            "overall_accuracy": round(overall_accuracy, 3),
        }

    def export_dp_stats(self, epsilon: float = 1.0) -> dict:
        """Return per-skill attempt counts with Laplace differential privacy noise."""
        rows = self._conn.execute(
            "SELECT skill, COUNT(*) as cnt, SUM(correct) as corr FROM attempts GROUP BY skill"
        ).fetchall()

        scale = 1.0 / epsilon
        result = {}
        for r in rows:
            # Laplace noise via sum of exponentials
            noise_cnt = random.expovariate(1 / scale) - random.expovariate(1 / scale)
            noise_corr = random.expovariate(1 / scale) - random.expovariate(1 / scale)
            result[r["skill"]] = {
                "attempts": max(0, round(r["cnt"] + noise_cnt)),
                "correct": max(0, round(r["corr"] + noise_corr)),
            }
        return result
