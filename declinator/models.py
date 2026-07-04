from django.db import models

class Noun(models.Model): 
    #base 
    basic_noun = models.CharField(max_length= 100)
    
    #gender
    gender = models.CharField(max_length=20, default="unknown")
    
    #singular 
    nominative_singular = models.CharField(max_length= 100) 
    genitive_singular = models.CharField(max_length= 100) 
    accusative_singular = models.CharField(max_length= 100) 
    vocative_singular = models.CharField(max_length= 100) 
    
    #plural 
    
    nominative_plural = models.CharField(max_length= 100) 
    genitive_plural = models.CharField(max_length= 100) 
    accusative_plural = models.CharField(max_length= 100) 
    vocative_plural = models.CharField(max_length= 100) 
    
    def __str__(self):
        return self.basic_noun
