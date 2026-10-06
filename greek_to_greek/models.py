from django.db import models

# Parts of speech allowed in content files; tier 1 uses noun and verb.
PARTS_OF_SPEECH = (
    "noun", "verb", "adjective", "adverb", "pronoun", "preposition",
    "conjunction", "numeral", "particle", "interjection", "phrase",
)


class GreekToGreek(models.Model):
    # Content-file identity: rows loaded from content/greek-to-greek/tier-N.json are matched on
    # (tier, content_id), the "tier" and "id" of each item, so reloading updates in place.
    tier = models.PositiveSmallIntegerField(default=1, db_index=True)
    content_id = models.PositiveIntegerField(null=True, blank=True)

    word = models.CharField(max_length=100, unique=True)
    pos = models.CharField(max_length=20, blank=True, default='')  # part of speech, see PARTS_OF_SPEECH
    explanation = models.TextField()  # monolingual definition, in Greek
    translations = models.JSONField(default=dict, blank=True)  # {"en": "person, human", ...}

    class Meta:
        ordering = ['word']
        constraints = [
            models.UniqueConstraint(fields=['tier', 'content_id'], name='greektogreek_tier_content_id_unique'),
        ]

    def __str__(self):
        return self.word
