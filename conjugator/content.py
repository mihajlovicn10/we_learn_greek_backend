"""
Load verb content files (content/verbs/tier-N.json, schema "verbs/v1") into the Verb table.

The files are the source of truth: loading a tier makes the table match the file
(creates new items, updates changed ones, deletes items removed from the file).
"""
import re

from we_learn_greek.content import check_greek, check_id, check_translations, nfc, sync_rows

from .models import Verb

SCHEMA = "verbs/v1"
ITEM_KEYS = {"id", "tier", "infinitive", "verb_type", "irregular", "translations", "conjugation"}
VERB_TYPE = re.compile(r"^(?:(?:A|B1|B2)(?:-passive)?|irregular)$")
MAX_FORM_LENGTH = Verb._meta.get_field("infinitive").max_length

# Tense key in the file -> field prefix on Verb (the API field names).
TENSES = {
    "present": "present",
    "imperfect": "imperfect",
    "aorist": "aorist",
    "future_continuous": "future_continuous",
    "future_simple": "future",
    "perfect": "perfect",
    "pluperfect": "plusperfect",
}
PERSONS = ("first_singular", "second_singular", "third_singular",
           "first_plural", "second_plural", "third_plural")


def field_name(prefix, person):
    if prefix == "present" and person == "third_plural":
        return "present_third_pluran"  # historical spelling, part of the public API
    return f"{prefix}_{person}"


def validate(data, expected_tier):
    """Return (rows, errors). rows are Verb field dicts, ready to save, only if errors is empty."""
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

    rows, seen_ids, seen_verbs = [], set(), set()
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
        if not isinstance(item["verb_type"], str) or not VERB_TYPE.match(item["verb_type"]):
            errors.append(f"{label}: verb_type must be A, B1 or B2 (optionally with -passive) or irregular, "
                          f"got {item['verb_type']!r}")
        if not isinstance(item["irregular"], bool):
            errors.append(f"{label}: irregular must be true or false")

        check_greek(errors, f"{label} infinitive", item["infinitive"], MAX_FORM_LENGTH)
        verb = nfc(item["infinitive"])
        if verb in seen_verbs:
            errors.append(f"{label}: duplicate infinitive {verb!r}")
        seen_verbs.add(verb)

        translations = check_translations(errors, label, item["translations"])

        forms = {}
        conjugation = item["conjugation"]
        if not isinstance(conjugation, dict) or set(conjugation) != set(TENSES):
            errors.append(f"{label}: conjugation must have exactly the tenses {list(TENSES)}")
            continue
        for tense, prefix in TENSES.items():
            persons = conjugation[tense]
            if persons is None:  # the tense doesn't exist for this verb (e.g. no aorist for είμαι)
                persons = [None] * len(PERSONS)
            elif not isinstance(persons, list) or len(persons) != len(PERSONS):
                errors.append(f"{label} {tense}: must be null or a list of {len(PERSONS)} forms "
                              f"(1st, 2nd, 3rd singular, then plural)")
                continue
            for person, form in zip(PERSONS, persons):
                if form is not None:  # a single missing person, e.g. impersonal verbs
                    check_greek(errors, f"{label} {tense}.{person}", form, MAX_FORM_LENGTH)
                forms[field_name(prefix, person)] = nfc(form)

        present = conjugation["present"]
        if not present or not any(present):
            errors.append(f"{label}: present is required")
        elif nfc(present[0]) != verb:
            errors.append(f"{label}: infinitive {verb!r} differs from present 1st singular {present[0]!r}")

        rows.append({
            "content_id": item_id,
            "tier": expected_tier,
            "infinitive": verb,
            "verb_type": item["verb_type"],
            "irregular": item["irregular"],
            "translations": translations,
            **forms,
        })
    return (rows if not errors else []), errors


def sync(rows, tier):
    return sync_rows(Verb, rows, tier=tier)
