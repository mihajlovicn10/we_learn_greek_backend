"""
Load noun content files (content/nouns/tier-N.json, schema "nouns/v1") into the Noun table.

The files are the source of truth: loading a tier makes the table match the file
(creates new items, updates changed ones, deletes items removed from the file).
"""
import unicodedata

from django.core.exceptions import ValidationError
from django.db import transaction

from dictionary.validators import validate_greek

from .models import Noun

SCHEMA = "nouns/v1"
GENDERS = {"masculine", "feminine", "neuter"}
NUMBERS = ("singular", "plural")
CASES = ("nominative", "genitive", "accusative", "vocative")
ITEM_KEYS = {"id", "tier", "basic_noun", "gender", "translations", "singular", "plural"}
MAX_FORM_LENGTH = Noun._meta.get_field("basic_noun").max_length


def _nfc(value):
    return unicodedata.normalize("NFC", value) if isinstance(value, str) else value


def _check_greek(errors, where, value):
    if not isinstance(value, str) or not value:
        errors.append(f"{where}: must be a non-empty string")
        return
    if len(value) > MAX_FORM_LENGTH:
        errors.append(f"{where}: longer than {MAX_FORM_LENGTH} characters")
    try:
        validate_greek(_nfc(value))
    except ValidationError:
        errors.append(f"{where}: {value!r} is not Greek letters with single spaces")


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
        if not isinstance(item_id, int) or isinstance(item_id, bool) or item_id < 1:
            errors.append(f"{label}: id must be a positive integer")
        elif item_id in seen_ids:
            errors.append(f"{label}: duplicate id")
        seen_ids.add(item_id)

        if item["tier"] != expected_tier:
            errors.append(f"{label}: tier is {item['tier']!r}, expected {expected_tier}")
        if item["gender"] not in GENDERS:
            errors.append(f"{label}: gender must be one of {sorted(GENDERS)}, got {item['gender']!r}")

        _check_greek(errors, f"{label} basic_noun", item["basic_noun"])
        word = _nfc(item["basic_noun"])
        if word in seen_words:
            errors.append(f"{label}: duplicate basic_noun {word!r}")
        seen_words.add(word)

        translations = item["translations"]
        if (not isinstance(translations, dict) or not translations
                or not all(isinstance(k, str) and len(k) == 2 and isinstance(v, str) and v.strip()
                           for k, v in translations.items())):
            errors.append(f'{label}: translations must map 2-letter language codes to text, e.g. {{"en": "..."}}')

        forms = {}
        for number in NUMBERS:
            block = item[number]
            if not isinstance(block, dict) or set(block) != set(CASES):
                errors.append(f"{label} {number}: must have exactly the cases {list(CASES)}")
                continue
            for case in CASES:
                value = block[case]
                if value is not None:  # null = the form doesn't exist (e.g. no plural)
                    _check_greek(errors, f"{label} {number}.{case}", value)
                forms[f"{case}_{number}"] = _nfc(value)
        if forms.get("nominative_singular") is None and "nominative_singular" in forms:
            errors.append(f"{label}: singular.nominative is required")
        elif forms.get("nominative_singular") not in (None, word):
            errors.append(f"{label}: basic_noun {word!r} differs from singular.nominative {forms['nominative_singular']!r}")

        rows.append({
            "content_id": item_id,
            "tier": expected_tier,
            "basic_noun": word,
            "gender": item["gender"],
            "translations": {k: v.strip() for k, v in translations.items()} if isinstance(translations, dict) else {},
            **forms,
        })
    return (rows if not errors else []), errors


@transaction.atomic
def sync(rows, tier):
    """Make the tier's rows match `rows`. Returns counts of created/updated/unchanged/deleted."""
    counts = {"created": 0, "updated": 0, "unchanged": 0, "deleted": 0}
    existing = {noun.content_id: noun for noun in Noun.objects.filter(tier=tier, content_id__isnull=False)}
    for row in rows:
        noun = existing.pop(row["content_id"], None)
        if noun is None:
            Noun.objects.create(**row)
            counts["created"] += 1
        elif any(getattr(noun, field) != value for field, value in row.items()):
            for field, value in row.items():
                setattr(noun, field, value)
            noun.save()
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1
    if existing:  # removed from the file
        counts["deleted"] = Noun.objects.filter(pk__in=[n.pk for n in existing.values()]).delete()[0]
    return counts
