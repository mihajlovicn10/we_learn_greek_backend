from django.db import models

class GreekToGreek(models.Model):
    word = models.CharField(max_length=100, unique=True)
    explanation = models.CharField(max_length=100)

    class Meta:
        ordering = ['word']

    def __str__(self):
        return self.word
