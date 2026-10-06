"""
Load noun content files (content/nouns/tier-N.json, schema "nouns/v1") into the Noun table.

The files are the source of truth: loading a tier makes the table match the file
(creates new items, updates changed ones, deletes items removed from the file).
"""
from we_learn_greek.content import check_greek, check_id, check_translations, nfc, sync_rows

from .models import Noun

SCHEMA = "nouns/v1"
GENDERS = {"masculine", "feminine", "neuter"}
NUMBERS = ("singular", "plural")
CASES = ("nominative", "genitive", "accusative", "vocative")
ITEM_KEYS = {"id", "tier", "basic_noun", "gender", "translations", "singular", "plural"}
MAX_FORM_LENGTH = Noun._meta.get_field("basic_noun").max_length


def validate(data, expected_tier):
    """Return (rows, errors). rows are Noun field dicts, ready to save, only if errors is empty."""
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
        if item["gender"] not in GENDERS:
            errors.append(f"{label}: gender must be one of {sorted(GENDERS)}, got {item['gender']!r}")

        check_greek(errors, f"{label} basic_noun", item["basic_noun"], MAX_FORM_LENGTH)
        word = nfc(item["basic_noun"])
        if word in seen_words:
            errors.append(f"{label}: duplicate basic_noun {word!r}")
        seen_words.add(word)

        translations = check_translations(errors, label, item["translations"])

        forms = {}
        for number in NUMBERS:
            block = item[number]
            if not isinstance(block, dict) or set(block) != set(CASES):
                errors.append(f"{label} {number}: must have exactly the cases {list(CASES)}")
                continue
            for case in CASES:
                value = block[case]
                if value is not None:  # null = the form doesn't exist (e.g. no plural)
                    check_greek(errors, f"{label} {number}.{case}", value, MAX_FORM_LENGTH)
                forms[f"{case}_{number}"] = nfc(value)
        if forms.get("nominative_singular") is None and "nominative_singular" in forms:
            errors.append(f"{label}: singular.nominative is required")
        elif forms.get("nominative_singular") not in (None, word):
            errors.append(f"{label}: basic_noun {word!r} differs from singular.nominative {forms['nominative_singular']!r}")

        rows.append({
            "content_id": item_id,
            "tier": expected_tier,
            "basic_noun": word,
            "gender": item["gender"],
            "translations": translations,
            **forms,
        })
    return (rows if not errors else []), errors


def sync(rows, tier):
    return sync_rows(Noun, rows, tier=tier)
