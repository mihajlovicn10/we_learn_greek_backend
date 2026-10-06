from django.db import models

class TransparentWord(models.Model): 
    # Content-file identity: rows loaded from content/transparent-words/<language>.json are matched
    # on (language, content_id), the item's "id", so reloading updates in place.
    tier = models.PositiveSmallIntegerField(default=1, db_index=True)
    content_id = models.PositiveIntegerField(null=True, blank=True)

    # Language info
    language = models.CharField(max_length=100, default='en', help_text="Language code (e.g., 'en', 'fr', 'de')")
    
    # Word data
    greek_word = models.CharField(max_length=100)
    language_word = models.CharField(max_length=100, blank=True, default='')
    pronunciation = models.CharField(max_length=100, blank=True, default='')
    etymology = models.TextField(blank=True)
    
    # Examples
    example_greek = models.TextField(blank=True)
    example_translation = models.TextField(blank=True)
    
    # Category
    category = models.CharField(max_length=100, default='other')
    
    class Meta:
        unique_together = ('language', 'greek_word')
        ordering = ['language', 'greek_word']
        constraints = [
            models.UniqueConstraint(fields=['language', 'content_id'], name='transparentword_language_content_id_unique'),
        ]
    
    def __str__(self):
        return f"{self.greek_word} → {self.language_word} ({self.language})" 