import random

FEEDBACK_POOL = {
    "kin": {
        "correct":       ["Byiza cyane, {name}!", "Ni byo!", "Wewe ni inzobere!"],
        "incorrect":     ["Gerageza nanone!", "Ntugire ubwoba, gerageza!"],
        "hint":          ["Bara kimwe kimwe.", "Reba neza ibishusho."],
        "encouragement": ["Komeza, {name}!", "Witeguye!"],
    },
    "fr": {
        "correct":       ["Bravo, {name}!", "Très bien!", "C'est exact!"],
        "incorrect":     ["Essaie encore!", "Ne t'inquiète pas, réessaie!"],
        "hint":          ["Compte un par un.", "Regarde bien l'image."],
        "encouragement": ["Continue, {name}!", "Tu es prêt!"],
    },
    "en": {
        "correct":       ["Great job, {name}!", "That's right!", "Well done!"],
        "incorrect":     ["Try again!", "Don't worry, give it another go!"],
        "hint":          ["Count one by one.", "Look carefully at the picture."],
        "encouragement": ["Keep going, {name}!", "You've got this!"],
    },
}

_FALLBACK_LANG = "en"


def _pool(lang: str, category: str) -> list:
    lang_pool = FEEDBACK_POOL.get(lang, FEEDBACK_POOL[_FALLBACK_LANG])
    return lang_pool.get(category, FEEDBACK_POOL[_FALLBACK_LANG].get(category, [""]))


def get_feedback(correct: bool, lang: str, child_name: str) -> str:
    category = "correct" if correct else "incorrect"
    template = random.choice(_pool(lang, category))
    return template.format(name=child_name)


def get_hint(item: dict, lang: str) -> str:
    hint_key = f"hint_{lang}" if lang in ("en", "fr", "kin") else "hint_en"
    if hint_key in item and item[hint_key]:
        return item[hint_key]
    return random.choice(_pool(lang, "hint"))


def get_encouragement(lang: str, child_name: str) -> str:
    template = random.choice(_pool(lang, "encouragement"))
    return template.format(name=child_name)
