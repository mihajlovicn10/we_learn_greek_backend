from django.db import models
from django.core.validators import RegexValidator 
from .validators import validate_greek
from we_learn_greek.models import User 

class Dictionary(models.Model):
    greek_word = models.CharField(
        max_length=30,
        validators=[validate_greek],
        help_text="Enter the word in Greek (only Greek Alphabet allowed, optionally with an article).",
    )
    pronounciation = models.CharField(
        max_length=30,
        null=False,
        blank=False,
        help_text="Enter the pronounciation (literally in latin script)",
    )
    translation = models.CharField(
        max_length=30,
        help_text="Enter the translation(s) in the desired language(s)",
    )
    date_added = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'greek_word')

    def __str__(self):
        return self.greek_word

