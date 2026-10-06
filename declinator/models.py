from django.db import models

class Noun(models.Model):
    # Content-file identity: rows loaded from content/nouns/tier-N.json are matched on
    # (tier, content_id), the "tier" and "id" of each item, so reloading updates in place.
    tier = models.PositiveSmallIntegerField(default=1, db_index=True)
    content_id = models.PositiveIntegerField(null=True, blank=True)

    #base
    basic_noun = models.CharField(max_length= 100)

    #gender
    gender = models.CharField(max_length=20, default="unknown")

    # {"en": "person, human", ...}
    translations = models.JSONField(default=dict, blank=True)

    # Case forms are null where the form doesn't exist (e.g. no plural for γάλα).

    #singular
    nominative_singular = models.CharField(max_length= 100, null=True, blank=True)
    genitive_singular = models.CharField(max_length= 100, null=True, blank=True)
    accusative_singular = models.CharField(max_length= 100, null=True, blank=True)
    vocative_singular = models.CharField(max_length= 100, null=True, blank=True)

    #plural

    nominative_plural = models.CharField(max_length= 100, null=True, blank=True)
    genitive_plural = models.CharField(max_length= 100, null=True, blank=True)
    accusative_plural = models.CharField(max_length= 100, null=True, blank=True)
    vocative_plural = models.CharField(max_length= 100, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tier', 'content_id'], name='noun_tier_content_id_unique'),
        ]

    def __str__(self):
        return self.basic_noun
