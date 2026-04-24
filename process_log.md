# Process Log

**Name**: Attahiru Jibril
**Date**: 2026-04-24

---

## Hour 1

- Designed the overall system architecture
- Set up project with `uv`, created directory skeleton
- Reviewed seed data in `res/curriculum_seed.json` (12 items across 5 skills: counting, number_sense, addition, subtraction, word_problem) and designed expansion rules per skill
- Used Claude Code to write `scripts/generate_data.py`, expanding the seed to 60 curriculum items

```text
Write scripts/generate_data.py that reads res/curriculum_seed.json and expands
it to 60+ items. Skills: counting (objects 1-10, 6 object types), number_sense
(compare pairs + before/after), addition (simple sums + Rwandan word problems
with mangoes/cows/RWF), subtraction (take-away + basket/market context),
word_problem (RWF, water point, mandazi contexts). Each item: id, skill,
difficulty 1-9, age_band, stem_en/fr/kin, visual ref string, answer_int,
distractors [answer-1, answer+1, answer+2] clamped to [0,20], hint_en, hint_kin.
Output: data/curriculum_full.json.
```