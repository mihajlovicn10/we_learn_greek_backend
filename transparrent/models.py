from django.db import models

class TransparentWord(models.Model): 
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
    
    def __str__(self):
        return f"{self.greek_word} → {self.language_word} ({self.language})" 