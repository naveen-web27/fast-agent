"""Explicit, versioned cultural conventions, never outcome predictions.

Background references: B. V. Raman, Muhurtha, chapter on marriage matching;
https://en.wikipedia.org/wiki/Nakshatra (27 equal divisions and naming padas);
https://www.sanskrit-lexicon.uni-koeln.de/ (Tamil Lexicon under Tamil dictionaries).
These references describe traditions, not evidence of predictive validity.
The local ten-check variant is unreviewed, omits regional exceptions, and must
not be represented as a certified reproduction of a particular publication.
"""

RULE_VERSION = "tamil-ten-check-educational-v1-unreviewed"
RULE_SOURCES = [
    {"reference": "B. V. Raman, Muhurtha, marriage matching chapter",
     "scope": "Background for star-count, gana, yoni, rajju and vedha conventions",
     "status": "Local tables and simplified decisions require practitioner review; not a critical edition"},
    {"reference": "https://en.wikipedia.org/wiki/Nakshatra",
     "scope": "27 nakshatras, four padas, naming convention background",
     "status": "Secondary source; does not validate compatibility outcomes"},
]
GANA = (
    "deva", "manushya", "rakshasa", "manushya", "deva", "manushya", "deva", "deva", "rakshasa",
    "rakshasa", "manushya", "manushya", "deva", "rakshasa", "deva", "rakshasa", "deva", "rakshasa",
    "rakshasa", "manushya", "manushya", "deva", "rakshasa", "rakshasa", "manushya", "manushya", "deva",
)
GANA_PASS = {
    "deva": {"deva": True, "manushya": True, "rakshasa": False},
    "manushya": {"deva": True, "manushya": True, "rakshasa": False},
    "rakshasa": {"deva": False, "manushya": False, "rakshasa": True},
}
YONI = (
    "horse", "elephant", "sheep", "snake", "snake", "dog", "cat", "sheep", "cat",
    "rat", "rat", "cow", "buffalo", "tiger", "buffalo", "tiger", "deer", "deer",
    "dog", "monkey", "mongoose", "monkey", "lion", "horse", "lion", "cow", "elephant",
)
YONI_OPPOSED = frozenset(frozenset(pair) for pair in (
    ("horse", "buffalo"), ("elephant", "lion"), ("sheep", "monkey"), ("snake", "mongoose"),
    ("dog", "deer"), ("cat", "rat"), ("cow", "tiger"),
))
RAJJU = (
    "foot", "thigh", "navel", "neck", "head", "neck", "navel", "thigh", "foot",
    "foot", "thigh", "navel", "neck", "head", "neck", "navel", "thigh", "foot",
    "foot", "thigh", "navel", "neck", "head", "neck", "navel", "thigh", "foot",
)
VEDHA_GROUPS = (
    frozenset((0, 17)), frozenset((1, 16)), frozenset((2, 15)), frozenset((3, 14)),
    frozenset((5, 21)), frozenset((6, 20)), frozenset((7, 19)), frozenset((8, 18)),
    frozenset((9, 26)), frozenset((10, 25)), frozenset((11, 24)), frozenset((12, 23)),
    frozenset((4, 13, 22)),
)
SIGN_LORDS = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
FRIENDS = {
    "Sun": frozenset(("Moon", "Mars", "Jupiter")),
    "Moon": frozenset(("Sun", "Mercury")),
    "Mars": frozenset(("Sun", "Moon", "Jupiter")),
    "Mercury": frozenset(("Sun", "Venus")),
    "Jupiter": frozenset(("Sun", "Moon", "Mars")),
    "Venus": frozenset(("Mercury", "Saturn")),
    "Saturn": frozenset(("Mercury", "Venus")),
}
ENEMIES = {
    "Sun": frozenset(("Venus", "Saturn")), "Moon": frozenset(),
    "Mars": frozenset(("Mercury",)), "Mercury": frozenset(("Moon",)),
    "Jupiter": frozenset(("Mercury", "Venus")), "Venus": frozenset(("Sun", "Moon")),
    "Saturn": frozenset(("Sun", "Moon", "Mars")),
}
VASIYA = ({4, 7}, {3, 6}, {5}, {7, 8}, {6}, {2, 11}, {5, 9}, {3}, {11}, {10}, {9}, {9})
DINA_COUNTS = frozenset(count for count in range(1, 28) if count % 9 in (0, 2, 4, 6, 8))
MAHENDRA_COUNTS = frozenset((4, 7, 10, 13, 16, 19, 22, 25))
STREE_COUNTS = frozenset(range(13, 28))
RASI_COUNTS = frozenset((7, 9, 10, 11, 12))


def porutham(bride_star: int, groom_star: int, bride_rasi: int, groom_rasi: int) -> dict:
    for value, ceiling in ((bride_star, 27), (groom_star, 27), (bride_rasi, 12), (groom_rasi, 12)):
        if type(value) is not int or not 0 <= value < ceiling:
            raise ValueError("Star and rasi indices must be zero-based integers in range")
    count = (groom_star - bride_star) % 27 + 1
    sign_count = (groom_rasi - bride_rasi) % 12 + 1
    bride_lord, groom_lord = SIGN_LORDS[bride_rasi], SIGN_LORDS[groom_rasi]
    lord_pass = (bride_lord == groom_lord or
                 (groom_lord not in ENEMIES[bride_lord] and bride_lord not in ENEMIES[groom_lord]
                  and (groom_lord in FRIENDS[bride_lord] or bride_lord in FRIENDS[groom_lord])))
    checks = (
        ("dina", count in DINA_COUNTS, {"inclusive_star_count": count, "allowed_counts": sorted(DINA_COUNTS)}),
        ("gana", GANA_PASS[GANA[bride_star]][GANA[groom_star]],
         {"bride": GANA[bride_star], "groom": GANA[groom_star], "rule": "same gana or deva/manushya"}),
        ("mahendra", count in MAHENDRA_COUNTS,
         {"inclusive_star_count": count, "allowed_counts": sorted(MAHENDRA_COUNTS)}),
        ("stree_deergha", count in STREE_COUNTS,
         {"inclusive_star_count": count, "allowed_counts": sorted(STREE_COUNTS)}),
        ("yoni", frozenset((YONI[bride_star], YONI[groom_star])) not in YONI_OPPOSED,
         {"bride": YONI[bride_star], "groom": YONI[groom_star], "rule": "not a listed opposed pair; no sex subdivision"}),
        ("rasi", sign_count in RASI_COUNTS,
         {"inclusive_sign_count": sign_count, "allowed_counts": sorted(RASI_COUNTS),
          "rule": "Conservative distance-only variant; same-sign and sign-lord exceptions omitted"}),
        ("rasi_adhipathi", lord_pass,
         {"bride_lord": bride_lord, "groom_lord": groom_lord,
          "rule": "same lord or at least one natural friendship with neither direction inimical"}),
        ("vasiya", groom_rasi in VASIYA[bride_rasi] or bride_rasi in VASIYA[groom_rasi],
         {"bride_targets": sorted(VASIYA[bride_rasi]), "groom_targets": sorted(VASIYA[groom_rasi]),
          "rule": "either-direction sign table; not five-category North Indian vashya"}),
        ("rajju", RAJJU[bride_star] != RAJJU[groom_star],
         {"bride_group": RAJJU[bride_star], "groom_group": RAJJU[groom_star],
          "rule": "different groups; ascending/descending exceptions omitted"}),
        ("vedha", not any(bride_star != groom_star and {bride_star, groom_star} <= group for group in VEDHA_GROUPS),
         {"rule": "no listed pair or head-rajju triple opposition", "bride_star": bride_star, "groom_star": groom_star}),
    )
    return {"variant": RULE_VERSION, "review_status": "unreviewed",
            "checks": [{"key": key, "matches_rule": bool(passed), "details": details} for key, passed, details in checks],
            "matched_count": sum(passed for _, passed, _ in checks), "total_checks": 10,
            "sources": RULE_SOURCES,
            "limitations": ["Count is not a marriage probability, recommendation, or measure of a person's worth.",
                            "Regional exceptions, same-star exceptions, full-chart synthesis and dosha are not implemented.",
                            "No medical, fertility, longevity or relationship-outcome inference is supported."]}


def reduce_number(number: int) -> int:
    if type(number) is not int or number < 0:
        raise ValueError("Use a nonnegative integer")
    while number > 9 and number not in (11, 22, 33):
        number = sum(int(digit) for digit in str(number))
    return number


GEMSTONES = {"Sun": "Ruby", "Moon": "Pearl", "Mars": "Red coral", "Mercury": "Emerald",
             "Jupiter": "Yellow sapphire", "Venus": "Diamond", "Saturn": "Blue sapphire",
             "Rahu": "Hessonite", "Ketu": "Cat's eye"}
VASTU_PREFERRED = {"facing": frozenset(("N", "NE", "E")), "main_door": frozenset(("N", "NE", "E")),
                   "kitchen": frozenset(("SE", "NW")), "bedroom": frozenset(("SW",))}

NAMING_SYLLABLES = (
    ("chu", "che", "cho", "la"), ("li", "lu", "le", "lo"), ("a", "i", "u", "e"),
    ("o", "va", "vi", "vu"), ("ve", "vo", "ka", "ki"), ("ku", "gha", "nga", "chha"),
    ("ke", "ko", "ha", "hi"), ("hu", "he", "ho", "da"), ("di", "du", "de", "do"),
    ("ma", "mi", "mu", "me"), ("mo", "ta", "ti", "tu"), ("te", "to", "pa", "pi"),
    ("pu", "sha", "na", "tha"), ("pe", "po", "ra", "ri"), ("ru", "re", "ro", "ta"),
    ("ti", "tu", "te", "to"), ("na", "ni", "nu", "ne"), ("no", "ya", "yi", "yu"),
    ("ye", "yo", "bha", "bhi"), ("bhu", "dha", "pha", "dhā"), ("bhe", "bho", "ja", "ji"),
    ("ju", "je", "jo", "khi"), ("ga", "gi", "gu", "ge"), ("go", "sa", "si", "su"),
    ("se", "so", "da", "di"), ("du", "tha", "jha", "nya"), ("de", "do", "cha", "chi"),
)
TAMIL_PREFIXES = {"a": ("அ",), "i": ("இ",), "u": ("உ",), "e": ("எ",),
                  "ka": ("க",), "ku": ("கு",), "ko": ("கோ",), "ma": ("ம",),
                  "mu": ("மு",), "pa": ("ப",), "pu": ("பு",), "po": ("பொ",),
                  "na": ("ந",), "ni": ("நி",), "ne": ("நெ",), "ya": ("ய",),
                  "va": ("வ",), "ve": ("வே",), "vi": ("வி",)}
NAME_LEXICON = "University of Madras Tamil Lexicon: https://dsal.uchicago.edu/dictionaries/tamil-lex/"
BABY_NAMES = (
    {"name_ta": "அருள்", "name_en": "Arul", "gender": "neutral", "syllable": "a", "meaning_ta": "கருணை", "meaning_en": "Grace; compassion", "lexeme": "அருள்"},
    {"name_ta": "அன்பு", "name_en": "Anbu", "gender": "neutral", "syllable": "a", "meaning_ta": "பாசம்", "meaning_en": "Love; affection", "lexeme": "அன்பு"},
    {"name_ta": "இனியன்", "name_en": "Iniyan", "gender": "male", "syllable": "i", "meaning_ta": "இனிமையானவன்", "meaning_en": "One who is sweet or pleasant", "lexeme": "இனியன்"},
    {"name_ta": "கயல்", "name_en": "Kayal", "gender": "female", "syllable": "ka", "meaning_ta": "ஒருவகை மீன்", "meaning_en": "A kind of fish", "lexeme": "கயல்"},
    {"name_ta": "மலர்", "name_en": "Malar", "gender": "female", "syllable": "ma", "meaning_ta": "பூ", "meaning_en": "Flower", "lexeme": "மலர்"},
    {"name_ta": "முகில்", "name_en": "Mugil", "gender": "neutral", "syllable": "mu", "meaning_ta": "மேகம்", "meaning_en": "Cloud", "lexeme": "முகில்"},
    {"name_ta": "நிலா", "name_en": "Nila", "gender": "female", "syllable": "ni", "meaning_ta": "நிலவு; நிலவொளி", "meaning_en": "Moon; moonlight", "lexeme": "நிலா"},
    {"name_ta": "யாழ்", "name_en": "Yaazh", "gender": "neutral", "syllable": "ya", "meaning_ta": "பழந்தமிழ் நரம்பிசைக்கருவி", "meaning_en": "An ancient Tamil stringed instrument", "lexeme": "யாழ்"},
    {"name_ta": "வேல்", "name_en": "Vel", "gender": "male", "syllable": "ve", "meaning_ta": "ஈட்டி", "meaning_en": "Spear", "lexeme": "வேல்"},
)


def name_matches(entry: dict, syllable: str) -> bool:
    return (entry["syllable"] == syllable and
            entry["name_en"].lower().startswith(syllable) and
            entry["name_ta"].startswith(TAMIL_PREFIXES.get(syllable, ("\0",))))


def baby_name_options(star: int, pada: int, gender: str) -> dict:
    if type(star) is not int or not 0 <= star < 27 or type(pada) is not int or not 1 <= pada <= 4:
        raise ValueError("Invalid nakshatra or pada")
    if gender not in ("neutral", "male", "female"):
        raise ValueError("Invalid gender")
    syllable = NAMING_SYLLABLES[star][pada - 1]
    names = [dict(entry, meaning_source=NAME_LEXICON) for entry in BABY_NAMES
             if (gender == "neutral" or entry["gender"] in (gender, "neutral")) and name_matches(entry, syllable)]
    return {"syllable": syllable, "tamil_prefixes": list(TAMIL_PREFIXES.get(syllable, ())), "names": names,
            "coverage": "curated_matches" if names else "no_curated_matches",
            "sources": [NAME_LEXICON, RULE_SOURCES[1]],
            "limitations": ["Small lexical-name collection; missing syllables return no suggestions.",
                            "Romanization is an explicit local convention, not an automatic Tamil transliterator.",
                            "Gender labels reflect common usage, not restrictions; neutral selection includes all names.",
                            "Meanings are lexical glosses, not invented compound etymologies; local usage may vary."]}