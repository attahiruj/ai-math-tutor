"""Curriculum data loader for AI math tutor."""

import csv
import json

REQUIRED_FIELDS = {"id", "skill", "difficulty", "answer_int", "stem_en", "visual"}
VALID_SKILLS = {"counting", "number_sense", "addition", "subtraction", "word_problem"}


def load_curriculum(path: str) -> list[dict]:
    """Load and validate a curriculum JSON file.

    Args:
        path: Path to a JSON file containing a list of curriculum items.

    Returns:
        A list of validated curriculum item dicts.

    Raises:
        ValueError: If the file cannot be decoded, is not a JSON array,
            or contains items missing required fields or unknown skills.
    """
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except UnicodeDecodeError:
        with open(path, encoding="latin-1") as f:
            items = json.load(f)
    if not isinstance(items, list):
        raise ValueError("{path}: expected a JSON array".format(path=path))
    for item in items:
        missing = REQUIRED_FIELDS - set(item.keys())
        if missing:
            raise ValueError("Item {id} missing fields: {missing}".format(id=item.get('id', '?'), missing=missing))
        if item['skill'] not in VALID_SKILLS:
            raise ValueError("Item {id}: unknown skill '{skill}'".format(id=item['id'], skill=item['skill']))
    return items
def get_items(
    items: list[dict],
    skill: str | None = None,
    difficulty_max: int | None = None,
) -> list[dict]:
    """Filter curriculum items by skill and maximum difficulty.

    Args:
        items: A list of curriculum item dicts.
        skill: Optional skill name to filter by.
        difficulty_max: Optional maximum difficulty (inclusive).

    Returns:
        A filtered list of curriculum items.
    """
    result = items
    if skill is not None:
        result = [x for x in result if x["skill"] == skill]
    if difficulty_max is not None:
        result = [x for x in result if x["difficulty"] <= difficulty_max]
    return result
def load_probes(path: str) -> list[dict]:
    """Load probe items from a CSV file.

    Args:
        path: Path to a CSV file with columns: id, skill, difficulty, answer_int.

    Returns:
        A list of probe item dicts.
    """
    probes = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            probes.append({
                "id": row["id"],
                "skill": row["skill"],
                "difficulty": int(row["difficulty"]),
                "answer_int": int(row["answer_int"]),
            })
    return probes
