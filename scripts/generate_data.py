"""Generate full curriculum JSON for AI math tutor."""

import json
import random
from pathlib import Path

SEED_PATH = Path("res/curriculum_seed.json")
OUT_JSON = Path("data/curriculum_full.json")

# ── Translation helpers ───────────────────────────────────────────────────────

OBJECTS_FR = {
    "apples": "pommes",
    "goats": "chèvres",
    "stars": "étoiles",
    "fish": "poissons",
    "fingers": "doigts",
    "mangoes": "mangues",
    "bananas": "bananes",
    "cows": "vaches",
    "eggs": "œufs",
    "beans": "haricots",
    "drums": "tambours",
    "beads": "perles",
}

OBJECTS_KIN = {
    "apples": "pome",
    "goats": "ihene",
    "stars": "inyenyeri",
    "fish": "ifi",
    "fingers": "intoki",
    "mangoes": "imyembe",
    "bananas": "ingizi",
    "cows": "inka",
    "eggs": "amagi",
    "beans": "ibishyimbo",
    "drums": "ingoma",
    "beads": "urunigi",
}
# ── Per-skill generators ──────────────────────────────────────────────────────


def make_distractors(answer: int) -> list[int]:
    """Generate plausible wrong answers for a given correct answer.

    Args:
        answer: The correct integer answer.

    Returns:
        A list of three plausible wrong integer answers.
    """
    cands = [answer - 1, answer + 1, answer + 2]
    cands = [max(0, min(20, c)) for c in cands]
    cands = list(dict.fromkeys(c for c in cands if c != answer))[:3]
    while len(cands) < 3:
        v = answer + len(cands) + 2
        if v != answer and v not in cands:
            cands.append(v)
    random.shuffle(cands)
    return cands


def gen_counting() -> list[dict]:
    """Generate counting curriculum items.

    Returns:
        A list of counting item dicts with English, French, and Kinyarwanda
        stems, visuals, answers, and distractors.
    """
    objects = [
        ("apples", "pommes", "pome"),
        ("goats", "chèvres", "ihene"),
        ("stars", "étoiles", "inyenyeri"),
        ("fish", "poissons", "ifi"),
        ("fingers", "doigts", "intoki"),
        ("mangoes", "mangues", "imyembe"),
    ]
    items = []
    for idx, count in enumerate(range(1, 11), start=1):
        obj_en, obj_fr, obj_kin = objects[idx % len(objects)]
        diff = max(1, min(3, 1 + (count - 1) // 4))
        age = "5-6" if diff <= 2 else "6-7"
        items.append(
            {
                "id": f"C{idx:03d}",
                "skill": "counting",
                "difficulty": diff,
                "age_band": age,
                "stem_en": f"How many {obj_en}?",
                "stem_fr": f"Combien de {obj_fr}?",
                "stem_kin": f"{obj_kin.capitalize()} zingahe?",
                "visual": f"{obj_en}_{count}",
                "answer_int": count,
                "distractors": make_distractors(count),
                "hint_en": "Count one by one.",
                "hint_kin": "Bara kimwe kimwe.",
            }
        )
    for idx, (count, obj_idx) in enumerate([(2, 4), (7, 5)], start=11):
        obj_en, obj_fr, obj_kin = objects[obj_idx % len(objects)]
        items.append(
            {
                "id": f"C{idx:03d}",
                "skill": "counting",
                "difficulty": 2,
                "age_band": "5-6",
                "stem_en": f"Count the {obj_en}. How many?",
                "stem_fr": f"Compte les {obj_fr}. Combien?",
                "stem_kin": f"Bara {obj_kin}. Zingahe?",
                "visual": f"{obj_en}_{count}",
                "answer_int": count,
                "distractors": make_distractors(count),
                "hint_en": "Point at each one as you count.",
                "hint_kin": "Tandika presi kuri buri kimwe.",
            }
        )
    return items


def gen_number_sense() -> list[dict]:
    """Generate number sense curriculum items.

    Returns:
        A list of number sense item dicts.
    """
    items = []
    idx = 1
    pairs = [(4, 7), (3, 8), (5, 9), (6, 2), (10, 7), (1, 9)]
    for a, b in pairs:
        bigger = max(a, b)
        diff = max(3, min(7, 4 + (bigger - 7) // 2))
        items.append(
            {
                "id": f"N{idx:03d}",
                "skill": "number_sense",
                "difficulty": diff,
                "age_band": "6-7" if diff <= 5 else "7-8",
                "stem_en": f"Which number is bigger: {a} or {b}?",
                "stem_fr": f"Quel nombre est plus grand: {a} ou {b}?",
                "stem_kin": f"Ni iyihe nimero nini: {a} cyangwa {b}?",
                "visual": f"compare_{a}_{b}",
                "answer_int": bigger,
                "distractors": make_distractors(bigger),
                "hint_en": "The farther right on the number line, the bigger.",
                "hint_kin": "Nimero nkuru iri iburyo bw'umurongo.",
            }
        )
        idx += 1
    befores = [
        (47, 49, 48),
        (14, 16, 15),
        (29, 31, 30),
        (8, 10, 9),
        (19, 21, 20),
        (5, 7, 6),
    ]
    for a, b, mid in befores:
        diff = max(4, min(7, 5 + (mid > 15) + (mid > 25)))
        items.append(
            {
                "id": f"N{idx:03d}",
                "skill": "number_sense",
                "difficulty": diff,
                "age_band": "7-8" if diff <= 6 else "8-9",
                "stem_en": f"What number comes between {a} and {b}?",
                "stem_fr": f"Quel nombre est entre {a} et {b}?",
                "stem_kin": f"Ni iyihe nimero iri hagati ya {a} na {b}?",
                "visual": f"numberline_{a}_{b}",
                "answer_int": mid,
                "distractors": make_distractors(mid),
                "hint_en": "Count up from the smaller number.",
                "hint_kin": "Bara uhereye kuri nimero ntoya.",
            }
        )
        idx += 1
    return items


def gen_addition() -> list[dict]:
    """Generate addition curriculum items.

    Returns:
        A list of addition item dicts.
    """
    items = []
    idx = 1
    simple = [
        (1, 1, "beads"),
        (2, 3, "beads"),
        (3, 4, "beads"),
        (4, 5, "mangoes"),
        (5, 4, "mangoes"),
        (6, 3, "mangoes"),
    ]
    for a, b, obj in simple:
        ans = a + b
        diff = max(3, min(7, 3 + (ans > 8) + (ans > 12)))
        items.append(
            {
                "id": f"A{idx:03d}",
                "skill": "addition",
                "difficulty": diff,
                "age_band": "6-7" if diff <= 5 else "7-8",
                "stem_en": f"{a} plus {b} equals?",
                "stem_fr": f"{a} plus {b} égale?",
                "stem_kin": f"{a} + {b} ni angahe?",
                "visual": f"{obj}_{a}_plus_{b}",
                "answer_int": ans,
                "distractors": make_distractors(ans),
                "hint_en": f"Use the {obj} to count.",
                "hint_kin": f"Koresha {OBJECTS_KIN.get(obj, obj)} kubara.",
            }
        )
        idx += 1
    word_probs = [
        (
            "Sara has 4 mangoes and gets 5 more. How many now?",
            "Sara a 4 mangues et en reçoit 5 de plus. Combien maintenant?",
            "Sara afite imyembe 4 aronka indi 5. Afite ingahe ubu?",
            9,
            "mangoes_4_plus_5",
            5,
        ),
        (
            "Kalisa has 6 cows. He buys 3 more. How many cows?",
            "Kalisa a 6 vaches. Il en achète 3 de plus. Combien?",
            "Kalisa afite inka 6. Agura indi 3. Afite inka zingahe?",
            9,
            "cows_6_plus_3",
            5,
        ),
        (
            "There are 7 bananas in a basket. We add 8. Total?",
            "Il y a 7 bananes dans un panier. On en ajoute 8. Total?",
            "Hari ingizi 7 mu gitebo. Twongeraho 8. Hamwe ni zingahe?",
            15,
            "bananas_7_plus_8",
            6,
        ),
        (
            "Amina scored 8 points. She scores 9 more. Total?",
            "Amina a marqué 8 points. Elle en marque 9 de plus. Total?",
            "Amina yahawe amanota 8. Aronka andi 9. Hamwe ni angahe?",
            17,
            "beads_8_plus_9",
            6,
        ),
        (
            "27 + 14 equals?",
            "27 + 14 égale?",
            "27 + 14 ni angahe?",
            41,
            "beads_27_plus_14",
            8,
        ),
        (
            "36 + 25 equals?",
            "36 + 25 égale?",
            "36 + 25 ni angahe?",
            61,
            "beads_36_plus_25",
            9,
        ),
    ]
    for en, fr, kin, ans, vis, diff in word_probs:
        items.append(
            {
                "id": f"A{idx:03d}",
                "skill": "addition",
                "difficulty": diff,
                "age_band": "7-8" if diff <= 6 else "8-9",
                "stem_en": en,
                "stem_fr": fr,
                "stem_kin": kin,
                "visual": vis,
                "answer_int": ans,
                "distractors": make_distractors(ans),
                "hint_en": "Add the ones first, then the tens.",
                "hint_kin": "Banza wongere ibirwa, hanyuma amajana.",
            }
        )
        idx += 1
    return items


def gen_subtraction() -> list[dict]:
    """Generate subtraction curriculum items.

    Returns:
        A list of subtraction item dicts.
    """
    items = []
    idx = 1
    simple = [
        (8, 3, "drums"),
        (10, 4, "drums"),
        (9, 2, "beans"),
        (7, 5, "beans"),
        (6, 1, "fingers"),
        (10, 6, "fingers"),
    ]
    for total, take, obj in simple:
        ans = total - take
        diff = max(4, min(8, 4 + (total > 8) + (total > 12)))
        items.append(
            {
                "id": f"S{idx:03d}",
                "skill": "subtraction",
                "difficulty": diff,
                "age_band": "7-8" if diff <= 6 else "8-9",
                "stem_en": f"{total} minus {take} equals?",
                "stem_fr": f"{total} moins {take} égale?",
                "stem_kin": f"{total} - {take} ni angahe?",
                "visual": f"{obj}_{total}_minus_{take}",
                "answer_int": ans,
                "distractors": make_distractors(ans),
                "hint_en": "Count back from the bigger number.",
                "hint_kin": "Subira uhereye kuri nimero nkuru.",
            }
        )
        idx += 1
    word_probs = [
        (
            "A basket has 12 beans. You eat 7. How many remain?",
            "Un panier a 12 haricots. Tu en manges 7. Combien restent?",
            "Igitebo gifite ibishyimbo 12. Urya 7. Hisigaye zingahe?",
            5,
            "beans_basket_12",
            6,
        ),
        (
            "There are 15 eggs. We sell 6. How many are left?",
            "Il y a 15 oeufs. On en vend 6. Combien restent?",
            "Hari amagi 15. Tugurisha 6. Hisigaye angahe?",
            9,
            "eggs_15_minus_6",
            6,
        ),
        (
            "Mama has 20 mangoes at the market. She sells 13. How many left?",
            "Mama a 20 mangues au marche. Elle en vend 13. Combien restent?",
            "Mama afite imyembe 20 ku isoko. Agurisha 13. Hisigaye zingahe?",
            7,
            "mangoes_market_20",
            7,
        ),
        (
            "A school has 18 chairs. 9 are taken away. How many remain?",
            "Une ecole a 18 chaises. 9 sont emportees. Combien restent?",
            "Ishuri rifite intebe 18. Batware 9. Hisigaye zingahe?",
            9,
            "chairs_18_minus_9",
            7,
        ),
        (
            "62 - 28 equals?",
            "62 - 28 egale?",
            "62 - 28 ni angahe?",
            34,
            "beads_62_minus_28",
            9,
        ),
        (
            "50 - 17 equals?",
            "50 - 17 egale?",
            "50 - 17 ni angahe?",
            33,
            "beads_50_minus_17",
            8,
        ),
    ]
    for en, fr, kin, ans, vis, diff in word_probs:
        items.append(
            {
                "id": f"S{idx:03d}",
                "skill": "subtraction",
                "difficulty": diff,
                "age_band": "7-8" if diff <= 6 else "8-9",
                "stem_en": en,
                "stem_fr": fr,
                "stem_kin": kin,
                "visual": vis,
                "answer_int": ans,
                "distractors": make_distractors(ans),
                "hint_en": "Start from the big number and count down.",
                "hint_kin": "Tangira kuri nimero nkuru usubire inyuma.",
            }
        )
        idx += 1
    return items


def gen_word_problem() -> list[dict]:
    """Generate word problem curriculum items.

    Returns:
        A list of word problem item dicts.
    """
    probs = [
        (
            "Three children share 9 cookies equally. How many does each get?",
            "Trois enfants partagent 9 biscuits. Combien chacun recoit?",
            "Abana batatu basangiye bisikwi 9. Umwana wese aronka zingahe?",
            3,
            "kids_3_cookies_9",
            6,
            "8-9",
        ),
        (
            "A tomato costs 100 RWF. Mama has 850 RWF. How many can she buy?",
            "Une tomate coute 100 RWF. Mama a 850 RWF. Combien peut-elle en acheter?",
            "Inyanya imwe igura amafaranga 100. Mama afite 850 RWF. Agura zingahe?",
            8,
            "rwf_850_tomato_100",
            8,
            "8-9",
        ),
        (
            "A water tank holds 20 litres. 8 litres are used. How many are left?",
            "Un reservoir contient 20 litres. On utilise 8 litres. Combien reste-t-il?",
            "Ikidendezi gifite litiro 20. Bakoresheje litiro 8. Hisigaye zingahe?",
            12,
            "water_tank_20",
            7,
            "8-9",
        ),
        (
            "Mandazi costs 50 RWF each. Jean has 400 RWF. How many can he buy?",
            "Un mandazi coute 50 RWF. Jean a 400 RWF. Combien peut-il en acheter?",
            "Mandazi imwe igura amafaranga 50. Jean afite 400 RWF. Agura zingahe?",
            8,
            "rwf_400_mandazi_50",
            8,
            "8-9",
        ),
        (
            "5 birds sit on a tree. 3 more arrive. How many birds total?",
            "5 oiseaux sont sur un arbre. 3 autres arrivent. Hamwe ni zingahe?",
            "Inyoni 5 zirimo ku giti. Izindi 3 zaza. Hamwe ni zingahe?",
            8,
            "birds_5_plus_3",
            6,
            "7-8",
        ),
        (
            "A farmer plants 4 rows of 3 seeds each. How many seeds?",
            "Un agriculteur plante 4 rangees de 3 graines. Combien de graines?",
            "Umuhinzi ahinga imirongo 4 y'imbuto 3 buri murongo. Imbuto zingahe?",
            12,
            "seeds_4_rows_3",
            7,
            "8-9",
        ),
        (
            "There are 16 pupils. 7 are absent. How many are present?",
            "Il y a 16 eleves. 7 sont absents. Combien sont presents?",
            "Hari abanyeshuri 16. 7 ntibabaho. Bangahe bahari?",
            9,
            "pupils_16_minus_7",
            6,
            "7-8",
        ),
        (
            "Amina has 3 bags of 5 oranges. How many oranges total?",
            "Amina a 3 sacs de 5 oranges. Combien d'oranges au total?",
            "Amina afite amasaho 3 y'imbuma 5 buri saho. Imbuma zingahe?",
            15,
            "oranges_3_bags_5",
            7,
            "8-9",
        ),
        (
            "A school collects 250 RWF Monday and 310 RWF Tuesday. Total?",
            "L'ecole collecte 250 RWF lundi et 310 RWF mardi. Total?",
            "Ishuri rikoranye 250 RWF kuwa mbere na 310 RWF kuwa kabiri. Hamwe ni angahe?",
            560,
            "rwf_250_plus_310",
            9,
            "8-9",
        ),
        (
            "If you have 6 apples and give away 4, how many do you have?",
            "Si tu as 6 pommes et en donnes 4, combien en as-tu?",
            "Niba ufite pome 6 ukabyereka 4, usigaye na zingahe?",
            2,
            "apples_6_minus_4",
            6,
            "7-8",
        ),
        (
            "Two baskets have 8 eggs each. How many eggs in total?",
            "Deux paniers ont 8 oeufs chacun. Combien d'oeufs au total?",
            "Ibikoresho bibiri bifite amagi 8 buri kari. Amagi angahe hamwe?",
            16,
            "eggs_2_baskets_8",
            7,
            "8-9",
        ),
        (
            "A rope is 15 m long. We cut off 6 m. How long is it now?",
            "Une corde mesure 15 m. On coupe 6 m. Quelle est sa longueur maintenant?",
            "Intambo ifite metero 15. Twagabanyije metero 6. Ifite metero zingahe ubu?",
            9,
            "rope_15_minus_6",
            7,
            "8-9",
        ),
    ]
