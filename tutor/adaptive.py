"""BKT knowledge tracing and adaptive item selection engine."""

import random
from collections import defaultdict, deque

SKILL_PARAMS = {
    "counting":     {"p_init": 0.30, "p_learn": 0.15, "p_forget": 0.01, "p_slip": 0.10, "p_guess": 0.25},
    "number_sense": {"p_init": 0.20, "p_learn": 0.12, "p_forget": 0.01, "p_slip": 0.12, "p_guess": 0.20},
    "addition":     {"p_init": 0.10, "p_learn": 0.10, "p_forget": 0.01, "p_slip": 0.15, "p_guess": 0.20},
    "subtraction":  {"p_init": 0.10, "p_learn": 0.08, "p_forget": 0.01, "p_slip": 0.15, "p_guess": 0.20},
    "word_problem": {"p_init": 0.05, "p_learn": 0.07, "p_forget": 0.01, "p_slip": 0.18, "p_guess": 0.15},
}

MASTERY_THRESHOLD = 0.90
_ELO_BASE = 700.0
_ELO_RANGE = 700.0  # difficulty 1→700, difficulty 9→1400
_ELO_K = 32


def _difficulty_to_elo(difficulty):
    return _ELO_BASE + (difficulty - 1) * (_ELO_RANGE / 8)


class BKTModel(object):
    """Bayesian Knowledge Tracing for a single skill."""

    def __init__(self, skill):
        params = SKILL_PARAMS[skill]
        self.p_learn = params["p_learn"]
        self.p_forget = params["p_forget"]
        self.p_slip = params["p_slip"]
        self.p_guess = params["p_guess"]
        self.p_mastery = params["p_init"]
        self.attempts = 0

    def update(self, correct):
        p = self.p_mastery
        slip, guess = self.p_slip, self.p_guess

        if correct:
            denom = p * (1 - slip) + (1 - p) * guess
            p_post = p * (1 - slip) / denom if denom > 0 else p
        else:
            denom = p * slip + (1 - p) * (1 - guess)
            p_post = p * slip / denom if denom > 0 else p

        p_next = p_post + (1 - p_post) * self.p_learn
        self.p_mastery = min(p_next, 1.0)
        self.attempts += 1

    def p_correct(self):
        """Expected P(correct) given current mastery."""
        return self.p_mastery * (1 - self.p_slip) + (1 - self.p_mastery) * self.p_guess


class EloBaseline(object):
    """Per-skill Elo rating for a student."""

    def __init__(self, initial_rating=1000.0):
        self.rating = initial_rating

    def update(self, difficulty, correct):
        item_elo = _difficulty_to_elo(difficulty)
        expected = 1.0 / (1.0 + 10 ** ((item_elo - self.rating) / 400))
        self.rating += _ELO_K * (float(correct) - expected)


class _StudentState(object):
    def __init__(self):
        self.bkt = {s: BKTModel(s) for s in SKILL_PARAMS}
        self.elo = {s: EloBaseline() for s in SKILL_PARAMS}
        self.recent = deque(maxlen=5)


class AdaptiveEngine(object):
    """Selects items and updates student models after each response."""

    def __init__(self, curriculum):
        self._curriculum = curriculum
        self._students = defaultdict(_StudentState)

    def _state(self, student_id):
        return self._students[student_id]

    def next_item(self, student_id):
        state = self._state(student_id)

        # 1. Skill with lowest mastery
        target_skill = min(
            SKILL_PARAMS,
            key=lambda s: state.bkt[s].p_mastery,
        )

        bkt = state.bkt[target_skill]
        p_est = bkt.p_correct()
        recent = set(state.recent)

        pool = [
            item for item in self._curriculum
            if item["skill"] == target_skill and item["id"] not in recent
        ]

        # 2. ZPD: items where P(correct) ∈ [0.65, 0.85]; since slip/guess are
        #    skill-level params, p_est is the same for all items in the skill —
        #    use difficulty to narrow when outside ZPD
        if 0.65 <= p_est <= 0.85 or not pool:
            candidates = pool
        else:
            # Outside ZPD: prefer easier items when struggling, harder when bored
            if p_est < 0.65:
                pool_sorted = sorted(pool, key=lambda i: i["difficulty"])
            else:
                pool_sorted = sorted(pool, key=lambda i: i["difficulty"], reverse=True)
            candidates = pool_sorted[:max(1, len(pool_sorted) // 2)]

        if not candidates:
            candidates = [i for i in self._curriculum if i["id"] not in recent]
        if not candidates:
            candidates = list(self._curriculum)

        return random.choice(candidates)

    def update(self, student_id, item_id, correct, response_time_ms):
        item = next((i for i in self._curriculum if i["id"] == item_id), None)
        if item is None:
            return

        state = self._state(student_id)
        skill = item["skill"]
        difficulty = item["difficulty"]

        state.bkt[skill].update(correct)
        state.elo[skill].update(difficulty, correct)
        state.recent.append(item_id)

    def get_mastery_summary(self, student_id):
        """Return {skill: p_mastery} for the given student."""
        state = self._state(student_id)
        return {skill: state.bkt[skill].p_mastery for skill in SKILL_PARAMS}
