import re
from django.core.exceptions import ValidationError

# Greek and Coptic letters (incl. all tonos/dialytika forms, upper and lower case, final sigma)
# plus the Greek Extended block for polytonic spelling.
_GREEK_LETTER = 'ΆΈ-ΊΌΎ-ΡΣ-ώἀ-῿'

# One or more Greek words separated by single spaces, e.g. "λόγος", "ο λόγος", "καλή τύχη".
GREEK_WORDS_RE = re.compile(rf'[{_GREEK_LETTER}]+( [{_GREEK_LETTER}]+)*')


def validate_greek(value):
    if not GREEK_WORDS_RE.fullmatch(value):
        raise ValidationError(
            "Only Greek letters are allowed, with single spaces between words.",
            code='invalid',
        )
