"""
Learner-friendly search: accent-insensitive for Greek, and Latin-letter input matches Greek words
("anthropos" finds "άνθρωπος", "kalimera" finds "Καλημέρα").

Matching runs in Python over the search fields rather than in SQL: accent folding and
transliteration aren't portable across SQLite and Postgres, and the word data is small,
read-only reference content (it is moving to static JSON, where this applies unchanged).

The frontend mirrors this logic in src/utils/greek.js. Keep the two in sync.
"""
import re
import unicodedata

from rest_framework import filters

_COMBINING = re.compile(r"[̀-ͯ]")


def normalize_greek(text):
    """Lowercase, strip accents/diaeresis, fold final sigma: "Άνθρωπος" -> "ανθρωποσ"."""
    text = unicodedata.normalize("NFD", text or "")
    return _COMBINING.sub("", text).lower().replace("ς", "σ").strip()


# Phonetic (how it sounds, not how it's spelled). Digraphs are checked before single letters.
_DIGRAPHS = {
    "ου": "ou", "αι": "e", "ει": "i", "οι": "i", "υι": "i",
    "μπ": "b", "ντ": "d", "γκ": "g", "γγ": "ng", "τσ": "ts", "τζ": "tz",
}
_LETTERS = {
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i", "θ": "th", "ι": "i",
    "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s",
    "τ": "t", "υ": "i", "φ": "f", "χ": "h", "ψ": "ps", "ω": "o",
}
# αυ/ευ sound like "av"/"ev" before vowels and voiced consonants, "af"/"ef" otherwise.
_VOICED_AFTER_U = set("αεηιουωβγδζλμνρ")


def transliterate(text):
    """Greek -> phonetic Latin, without accents: "ευχαριστώ" -> "efharisto"."""
    chars = normalize_greek(text)
    out = []
    i = 0
    while i < len(chars):
        char, nxt = chars[i], chars[i + 1] if i + 1 < len(chars) else ""
        if char in "αε" and nxt == "υ":
            after = chars[i + 2] if i + 2 < len(chars) else ""
            out.append(("a" if char == "α" else "e") + ("v" if after in _VOICED_AFTER_U and after else "f"))
            i += 2
        elif char + nxt in _DIGRAPHS:
            out.append(_DIGRAPHS[char + nxt])
            i += 2
        else:
            out.append(_LETTERS.get(char, char))
            i += 1
    return "".join(out)


_LOOSE_RULES = [
    (r"ph", "f"), (r"(kh|ch)", "h"), (r"dh", "d"), (r"mp", "b"), (r"b", "v"), (r"nt", "d"),
    (r"(gk|gg)", "g"), (r"ks", "x"), (r"ai", "e"), (r"(ei|oi|yi|y)", "i"), (r"ou", "u"),
    (r"w", "o"), (r"(.)\1+", r"\1"),
]


def loose_latin(text):
    """Collapse spelling variants learners use for one sound: philosophia ~ filosofia, mpira ~ bira."""
    text = normalize_greek(text)
    for pattern, replacement in _LOOSE_RULES:
        text = re.sub(pattern, replacement, text)
    return text


_LATIN = re.compile(r"[a-z]", re.IGNORECASE)


def matches(value, query):
    """True if `query` matches `value`: accent-insensitive, and Latin input matches Greek words."""
    if not query or not query.strip():
        return True
    if not value:
        return False
    if normalize_greek(query) in normalize_greek(value):
        return True
    if not _LATIN.search(query):
        return False
    return loose_latin(query) in loose_latin(transliterate(value))


class GreekSearchFilter(filters.SearchFilter):
    """
    Drop-in for DRF's SearchFilter (same `?search=` param and `search_fields`), using `matches`.
    Every space-separated term must match at least one search field, as in SearchFilter.
    """

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        terms = self.get_search_terms(request)
        if not search_fields or not terms:
            return queryset

        fields = [field.lstrip("^=@$") for field in search_fields]
        matching_pks = [
            row[0]
            for row in queryset.values_list("pk", *fields)
            if all(any(matches(value, term) for value in row[1:]) for term in terms)
        ]
        return queryset.filter(pk__in=matching_pks)
