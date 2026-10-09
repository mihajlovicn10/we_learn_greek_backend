"""
Load transparent-word content files (content/transparent-words/<language>.json, schema "transparent/v1")
into the TransparentWord table.

Unlike the other content types these files are per language, not per tier: each file holds every
tier for one language, and each item carries its own "tier". Loading a file makes that language's
rows match it (creates new items, updates changed ones, deletes items removed from the file).
"""
import re

from we_learn_greek.content import check_greek, check_id, nfc, sync_rows

from .models import TransparentWord

SCHEMA = "transparent/v1"
FILE_NAME = re.compile(r"^([a-z]{2})\.json$")
FILE_NAME_HINT = "<language code>.json, e.g. en.json"

# The languages the frontend offers (src/pages/TransparentWords.jsx KNOWN_LANGUAGES). ISO 639-1
# codes: Ukrainian is "uk" (the frontend shows it as "UA").
LANGUAGES = ("en", "fr", "de", "es", "ru", "it", "sr", "uk", "ar")
CATEGORIES = (
    "Arts", "Education", "Everyday", "Food", "Health",
    "Nature", "Philosophy", "Science", "Society", "Technology",
)
ITEM_KEYS = {"id", "tier", "language", "greek_word", "language_word", "pronunciation",
             "etymology", "example_greek", "example_translation", "category"}
GREEK_LETTER = re.compile(r"[Ά-ώἀ-῿]")
MAX_TEXT_LENGTH = 500


def _field_max(name):
    return TransparentWord._meta.get_field(name).max_length or MAX_TEXT_LENGTH


def _text(errors, label, item, key, greek=False):
    value = item[key]
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} {key}: must be non-empty text")
        return ""
    value = nfc(value.strip())
    if len(value) > _field_max(key):
        errors.append(f"{label} {key}: longer than {_field_max(key)} characters")
    if greek and not GREEK_LETTER.search(value):
        errors.append(f"{label} {key}: must be written in Greek")
    return value


def validate(data, language):
    """Return (rows, errors). rows are TransparentWord field dicts, ready to save, only if errors is empty."""
    errors = []
    if language not in LANGUAGES:
        return [], [f"language {language!r} is not supported; use one of {list(LANGUAGES)}"]
    if not isinstance(data, dict):
        return [], ["file must contain a JSON object"]
    if data.get("schema") != SCHEMA:
        errors.append(f'"schema" must be "{SCHEMA}", got {data.get("schema")!r}')
    if data.get("language") != language:
        errors.append(f'"language" is {data.get("language")!r} but the file name says {language!r}')
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return [], errors + ['"items" must be a non-empty list']

    rows, seen_ids, seen_words = [], set(), set()
    for index, item in enumerate(items):
        label = f"item {item.get('id', f'#{index}')}" if isinstance(item, dict) else f"item #{index}"
        if not isinstance(item, dict):
            errors.append(f"{label}: must be an object")
            continue
        if set(item) != ITEM_KEYS:
            missing, extra = ITEM_KEYS - set(item), set(item) - ITEM_KEYS
            errors.append(f"{label}: missing keys {sorted(missing)}, unexpected keys {sorted(extra)}")
            continue

        check_id(errors, label, item["id"], seen_ids)
        tier = item["tier"]
        if not isinstance(tier, int) or isinstance(tier, bool) or not 1 <= tier <= 5:
            errors.append(f"{label}: tier must be a whole number from 1 to 5")
        if item["language"] != language:
            errors.append(f"{label}: language is {item['language']!r}, expected {language!r}")
        if item["category"] not in CATEGORIES:
            errors.append(f"{label}: category must be one of {list(CATEGORIES)}, got {item['category']!r}")

        check_greek(errors, f"{label} greek_word", item["greek_word"], _field_max("greek_word"))
        word = nfc(item["greek_word"])
        if word in seen_words:
            errors.append(f"{label}: duplicate greek_word {word!r}")
        seen_words.add(word)

        rows.append({
            "content_id": item["id"],
            "tier": tier,
            "language": language,
            "greek_word": word,
            "language_word": _text(errors, label, item, "language_word"),
            "pronunciation": _text(errors, label, item, "pronunciation"),
            "etymology": _text(errors, label, item, "etymology"),
            "example_greek": _text(errors, label, item, "example_greek", greek=True),
            "example_translation": _text(errors, label, item, "example_translation"),
            "category": item["category"],
        })
    return (rows if not errors else []), errors


def sync(rows, language):
    return sync_rows(TransparentWord, rows, language=language)
