from django.db import models

class Verb(models.Model):
    # Content-file identity: rows loaded from content/verbs/tier-N.json are matched on
    # (tier, content_id), the "tier" and "id" of each item, so reloading updates in place.
    tier = models.PositiveSmallIntegerField(default=1, db_index=True)
    content_id = models.PositiveIntegerField(null=True, blank=True)

    infinitive = models.CharField(max_length=100, unique=True)
    # Conjugation group: A, B1, B2, A-passive, B1-passive, irregular.
    verb_type = models.CharField(max_length=10)
    irregular = models.BooleanField(default=False)
    # {"en": "to write", ...}
    translations = models.JSONField(default=dict, blank=True)

    # Tense forms are null where the tense doesn't exist (e.g. no aorist for είμαι).
    # Present is always required.
    
    #Conjugation for Present Tense 
    
    present_first_singular = models.CharField(max_length=100) 
    present_second_singular = models.CharField(max_length= 100) 
    present_third_singular = models.CharField(max_length=100)
    present_first_plural = models.CharField(max_length=100) 
    present_second_plural = models.CharField(max_length=100)
    present_third_pluran = models.CharField(max_length=100)
    
    
    # Conjugation for aorist 
    
    aorist_first_singular = models.CharField(max_length=100, null=True, blank=True) 
    aorist_second_singular = models.CharField(max_length=100, null=True, blank=True)
    aorist_third_singular = models.CharField(max_length=100, null=True, blank=True)
    aorist_first_plural = models.CharField(max_length=100, null=True, blank=True)
    aorist_second_plural = models.CharField(max_length=100, null=True, blank=True)
    aorist_third_plural = models.CharField(max_length=100, null=True, blank=True)
    
    #Conjugation for Imperfect 
    
    imperfect_first_singular = models.CharField(max_length=100, null=True, blank=True)
    imperfect_second_singular = models.CharField(max_length=100, null=True, blank=True)
    imperfect_third_singular = models.CharField(max_length=100, null=True, blank=True)
    imperfect_first_plural = models.CharField(max_length=100, null=True, blank=True)
    imperfect_second_plural = models.CharField(max_length=100, null=True, blank=True)
    imperfect_third_plural = models.CharField(max_length=100, null=True, blank=True) 
    
    #Conjugation for Perfect 
    
    perfect_first_singular = models.CharField(max_length=100, null=True, blank=True) 
    perfect_second_singular = models.CharField(max_length=100, null=True, blank=True)
    perfect_third_singular = models.CharField(max_length=100, null=True, blank=True) 
    perfect_first_plural = models.CharField(max_length=100, null=True, blank=True) 
    perfect_second_plural = models.CharField(max_length=100, null=True, blank=True)
    perfect_third_plural = models.CharField(max_length=100, null=True, blank=True) 
    
    #Conjugation for Plusperfect 
    
    plusperfect_first_singular = models.CharField(max_length=100, null=True, blank=True) 
    plusperfect_second_singular = models.CharField(max_length=100, null=True, blank=True) 
    plusperfect_third_singular = models.CharField(max_length=100, null=True, blank=True) 
    plusperfect_first_plural = models.CharField(max_length=100, null=True, blank=True) 
    plusperfect_second_plural = models.CharField(max_length=100, null=True, blank=True) 
    plusperfect_third_plural = models.CharField(max_length=100, null=True, blank=True) 
    
    #Conjugation for Future (simple future / στιγμιαίος μέλλοντας: θα γράψω)
    
    future_first_singular = models.CharField(max_length=100, null=True, blank=True) 
    future_second_singular = models.CharField(max_length=100, null=True, blank=True) 
    future_third_singular = models.CharField(max_length=100, null=True, blank=True) 
    future_first_plural = models.CharField(max_length=100, null=True, blank=True) 
    future_second_plural = models.CharField(max_length=100, null=True, blank=True) 
    future_third_plural = models.CharField(max_length=100, null=True, blank=True) 

    # Conjugation for Future Continuous (εξακολουθητικός μέλλοντας: θα γράφω).
    # Nullable so verbs added before this tense existed stay valid.

    future_continuous_first_singular = models.CharField(max_length=100, null=True, blank=True)
    future_continuous_second_singular = models.CharField(max_length=100, null=True, blank=True)
    future_continuous_third_singular = models.CharField(max_length=100, null=True, blank=True)
    future_continuous_first_plural = models.CharField(max_length=100, null=True, blank=True)
    future_continuous_second_plural = models.CharField(max_length=100, null=True, blank=True)
    future_continuous_third_plural = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tier', 'content_id'], name='verb_tier_content_id_unique'),
        ]

    def __str__(self):
        return self.infinitive
    