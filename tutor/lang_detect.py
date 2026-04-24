import re

# Token dictionaries per language (sets for O(1) lookup)
_KIN_WORDS = {
    "rimwe",
    "kabiri",
    "gatatu",
    "kane",
    "gatanu",
    "gatandatu",
    "indwi",
    "umunani",
    "icyenda",
    "icumi",
    "makumyabiri",
    "nde",
    "ni",
    "iki",
    "bite",
    "muraho",
    "yego",
    "oya",
    "ese",
    "kandi",
    "ariko",
    "neza",
    "cyane",
    "gato",
    "bara",
    "reba",
    "gerageza",
    "komeza",
}

_FR_WORDS = {
    "un",
    "deux",
    "trois",
    "quatre",
    "cinq",
    "six",
    "sept",
    "huit",
    "neuf",
    "dix",
    "vingt",
    "le",
    "la",
    "les",
    "de",
    "du",
    "et",
    "est",
    "pas",
    "non",
    "oui",
    "bonjour",
    "merci",
    "bien",
    "tres",
    "essaie",
    "encore",
    "bravo",
    "combien",
}

_EN_WORDS = {
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "twenty",
    "the",
    "a",
    "is",
    "are",
    "and",
    "no",
    "yes",
    "not",
    "how",
    "many",
    "count",
    "hello",
    "great",
    "good",
    "try",
    "again",
    "well",
    "done",
}

# Number words mapped to their language
_NUM_LANG = {}
for w in [
    "rimwe",
    "kabiri",
    "gatatu",
    "kane",
    "gatanu",
    "gatandatu",
    "indwi",
    "umunani",
    "icyenda",
    "icumi",
    "makumyabiri",
]:
    _NUM_LANG[w] = "kin"
for w in [
    "un",
    "deux",
    "trois",
    "quatre",
    "cinq",
    "six",
    "sept",
    "huit",
    "neuf",
    "dix",
    "vingt",
]:
    _NUM_LANG[w] = "fr"
for w in [
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "twenty",
]:
    _NUM_LANG[w] = "en"


def _tokenize(text):
    return re.findall(r"[a-zA-Z\x80-\xff]+", text.lower())


def detect_language(text):
    tokens = _tokenize(text)
    if not tokens:
        return "en"

    counts = {"kin": 0, "fr": 0, "en": 0}
    num_lang = None

    for tok in tokens:
        if tok in _KIN_WORDS:
            counts["kin"] += 1
        if tok in _FR_WORDS:
            counts["fr"] += 1
        if tok in _EN_WORDS:
            counts["en"] += 1
        if tok in _NUM_LANG:
            num_lang = _NUM_LANG[tok]

    total = len(tokens)
    dominant = max(counts, key=lambda k: counts[k])

    # If dominant language has fewer than 20% of tokens matched, fall back to "en"
    if counts[dominant] == 0:
        dominant = "en"

    kin_ratio = counts["kin"] / total if total > 0 else 0
    if kin_ratio > 0.30:
        dominant = "kin"

    # Mixed: number word is in a different language than dominant
    if num_lang is not None and num_lang != dominant:
        return "mix"

    return dominant


def get_reply_config(detected, session_lang):
    """Return (reply_lang, embed_num_lang).

    If mixed, mirror the dominant language and embed the secondary language
    for number words. Otherwise reply in the dominant (or session) language.
    """
    dom = detected.get("dominant", session_lang)
    is_mixed = detected.get("is_mixed", False)
    num_lang = detected.get("num_lang")

    if is_mixed and num_lang and num_lang != dom:
        return dom, num_lang
    return dom, None


def detect_language_full(text):
    """Extended detection returning {dominant, is_mixed, num_lang}."""
    tokens = _tokenize(text)
    if not tokens:
        return {"dominant": "en", "is_mixed": False, "num_lang": None}

    counts = {"kin": 0, "fr": 0, "en": 0}
    num_langs = []

    for tok in tokens:
        if tok in _KIN_WORDS:
            counts["kin"] += 1
        if tok in _FR_WORDS:
            counts["fr"] += 1
        if tok in _EN_WORDS:
            counts["en"] += 1
        if tok in _NUM_LANG:
            num_langs.append(_NUM_LANG[tok])

    total = len(tokens)
    dominant = max(counts, key=lambda k: counts[k])
    if counts[dominant] == 0:
        dominant = "en"

    kin_ratio = counts["kin"] / total if total > 0 else 0
    if kin_ratio > 0.30:
        dominant = "kin"

    num_lang = num_langs[0] if num_langs else None
    is_mixed = num_lang is not None and num_lang != dominant

    return {"dominant": dominant, "is_mixed": is_mixed, "num_lang": num_lang}


def dominant_language(detected, session_lang):
    """Return the language to reply in, given a detect_language() result."""
    if detected == "mix":
        return session_lang
    return detected
