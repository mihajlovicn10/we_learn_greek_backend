"""
Load Greek-to-Greek content files (content/greek-to-greek/tier-N.json, schema "greek-to-greek/v1")
into the GreekToGreek table.

The files are the source of truth: loading a tier makes the table match the file
(creates new items, updates changed ones, deletes items removed from the file).
"""
import re

from we_learn_greek.content import check_greek, check_id, check_translations, nfc, sync_rows

from .models import PARTS_OF_SPEECH, GreekToGreek

SCHEMA = "greek-to-greek/v1"
ITEM_KEYS = {"id", "tier", "word", "pos", "explanation", "translations"}
MAX_WORD_LENGTH = GreekToGreek._meta.get_field("word").max_length
MAX_EXPLANATION_LENGTH = 500
GREEK_LETTER = re.compile(r"[Ά-ώἀ-῿]")


def validate(data, expected_tier):
    """Return (rows, errors). rows are GreekToGreek field dicts, ready to save, only if errors is empty."""
    errors = []
    if not isinstance(data, dict):
        return [], ["file must contain a JSON object"]
    if data.get("schema") != SCHEMA:
        errors.append(f'"schema" must be "{SCHEMA}", got {data.get("schema")!r}')
    if data.get("tier") != expected_tier:
        errors.append(f'"tier" is {data.get("tier")!r} but the file name says tier {expected_tier}')
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

        item_id = item["id"]
        check_id(errors, label, item_id, seen_ids)
        if item["tier"] != expected_tier:
            errors.append(f"{label}: tier is {item['tier']!r}, expected {expected_tier}")
        if item["pos"] not in PARTS_OF_SPEECH:
            errors.append(f"{label}: pos must be one of {list(PARTS_OF_SPEECH)}, got {item['pos']!r}")

        check_greek(errors, f"{label} word", item["word"], MAX_WORD_LENGTH)
        word = nfc(item["word"])
        if word in seen_words:
            errors.append(f"{label}: duplicate word {word!r}")
        seen_words.add(word)

        explanation = item["explanation"]
        if not isinstance(explanation, str) or not explanation.strip():
            errors.append(f"{label} explanation: must be non-empty text")
            explanation = ""
        else:
            explanation = nfc(explanation.strip())
            if len(explanation) > MAX_EXPLANATION_LENGTH:
                errors.append(f"{label} explanation: longer than {MAX_EXPLANATION_LENGTH} characters")
            if not GREEK_LETTER.search(explanation):
                errors.append(f"{label} explanation: must be written in Greek")

        rows.append({
            "content_id": item_id,
            "tier": expected_tier,
            "word": word,
            "pos": item["pos"],
            "explanation": explanation,
            "translations": check_translations(errors, label, item["translations"]),
        })
    return (rows if not errors else []), errors


def sync(rows, tier):
    return sync_rows(GreekToGreek, rows, tier)
