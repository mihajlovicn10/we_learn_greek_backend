"""Helpers shared by the per-type content loaders (declinator/content.py, conjugator/content.py)."""
import unicodedata

from django.core.exceptions import ValidationError
from django.db import transaction

from dictionary.validators import validate_greek


def nfc(value):
    return unicodedata.normalize("NFC", value) if isinstance(value, str) else value


def check_greek(errors, where, value, max_length):
    if not isinstance(value, str) or not value:
        errors.append(f"{where}: must be a non-empty string")
        return
    if len(value) > max_length:
        errors.append(f"{where}: longer than {max_length} characters")
    try:
        validate_greek(nfc(value))
    except ValidationError:
        errors.append(f"{where}: {value!r} is not Greek letters with single spaces")


def check_translations(errors, label, translations):
    if (not isinstance(translations, dict) or not translations
            or not all(isinstance(k, str) and len(k) == 2 and isinstance(v, str) and v.strip()
                       for k, v in translations.items())):
        errors.append(f'{label}: translations must map 2-letter language codes to text, e.g. {{"en": "..."}}')
        return {}
    return {k: v.strip() for k, v in translations.items()}


def check_id(errors, label, item_id, seen_ids):
    if not isinstance(item_id, int) or isinstance(item_id, bool) or item_id < 1:
        errors.append(f"{label}: id must be a positive integer")
    elif item_id in seen_ids:
        errors.append(f"{label}: duplicate id")
    seen_ids.add(item_id)


@transaction.atomic
def sync_rows(model, rows, **scope):
    """Make the rows of `model` that one file owns (`scope`, e.g. tier=1 or language="en")
    match `rows`, matched on content_id. Returns counts of created/updated/unchanged/deleted."""
    counts = {"created": 0, "updated": 0, "unchanged": 0, "deleted": 0}
    existing = {obj.content_id: obj for obj in model.objects.filter(**scope, content_id__isnull=False)}
    to_create = []
    for row in rows:
        obj = existing.pop(row["content_id"], None)
        if obj is None:
            to_create.append(row)
        elif any(getattr(obj, field) != value for field, value in row.items()):
            for field, value in row.items():
                setattr(obj, field, value)
            obj.save()
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1
    if existing:  # removed from the file; delete first so a re-added unique value can't collide
        counts["deleted"] = model.objects.filter(pk__in=[o.pk for o in existing.values()]).delete()[0]
    for row in to_create:
        model.objects.create(**row)
    counts["created"] = len(to_create)
    return counts
