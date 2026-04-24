"""Visual parsing module for AI math tutor."""

import re

_LAYOUT_RULES = {
    "fingers": "row",
    "beads": "row",
}

_KNOWN_SHAPES = {
    "apples", "goats", "stars", "fish", "fingers", "mangoes", "cows", "water",
    "mandazi", "beads", "bananas", "drums", "beans", "tomatoes", "birds", "seeds",
    "pupils", "oranges", "frogs", "balls", "eggs", "chairs", "cookies", "kids", "rope",
}


def _base_shape(name: str) -> str:
    """Return the first known renderable shape word from a compound name like 'beans_basket'."""
    for part in name.split("_"):
        if part in _KNOWN_SHAPES:
            return part
    return name.split("_")[0]


def parse_visual(visual: str) -> dict:
    """Translate a visual string into scene metadata.

    Supported patterns:
      numberline_{a}_{b}       → comparison (number-sense ordering)
      compare_{a}_{b}          → comparison between two numbers
      {shape}_{a}_plus_{b}     → addition scene
      {shape}_{a}_minus_{b}    → subtraction scene
      {s1}_{n1}_{s2}_{n2}      → word-problem scene (two object groups)
      {shape}_{count}          → simple counting scene
    """
    if not visual:
        return {"type": "static", "shape": "", "count": 0, "layout": "static"}

    # numberline_{a}_{b}
    m = re.fullmatch(r"numberline_(\d+)_(\d+)", visual)
    if m:
        return {"type": "comparison", "a": int(m.group(1)), "b": int(m.group(2))}

    # compare_{a}_{b}
    m = re.fullmatch(r"compare_(\d+)_(\d+)", visual)
    if m:
        return {"type": "comparison", "a": int(m.group(1)), "b": int(m.group(2))}

    # {shape}_{a}_plus_{b}
    m = re.fullmatch(r"(.+?)_(\d+)_plus_(\d+)", visual)
    if m:
        shape = _base_shape(m.group(1))
        return {
            "type": "addition",
            "shape": shape,
            "a": int(m.group(2)),
            "b": int(m.group(3)),
            "layout": _LAYOUT_RULES.get(shape, "row"),
        }

    # {shape}_{a}_minus_{b}
    m = re.fullmatch(r"(.+?)_(\d+)_minus_(\d+)", visual)
    if m:
        shape = _base_shape(m.group(1))
        return {
            "type": "subtraction",
            "shape": shape,
            "a": int(m.group(2)),
            "b": int(m.group(3)),
            "layout": _LAYOUT_RULES.get(shape, "scatter"),
        }

    # {s1}_{n1}_{s2}_{n2}  — word-problem with two distinct object groups
    m = re.fullmatch(r"([a-z]+)_(\d+)_([a-z]+)_(\d+)", visual)
    if m:
        return {
            "type": "word_problem",
            "shape1": m.group(1),
            "n1": int(m.group(2)),
            "shape2": m.group(3),
            "n2": int(m.group(4)),
        }

    # {shape}_{count}  — simple counting (compound shape names normalised to base)
    parts = visual.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        shape = _base_shape(parts[0])
        count = int(parts[1])
        layout = _LAYOUT_RULES.get(shape, "scatter")
        return {"type": "counting", "shape": shape, "count": count, "layout": layout}

    return {"type": "static", "shape": visual, "count": 0, "layout": "static"}
