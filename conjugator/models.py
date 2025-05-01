from django.db import models

class Verb(models.Model):
    infinitive = models.CharField(max_length=100, unique=True)
    verb_type = models.CharField(max_length=10) #Type of the verb (e.g. A1, B1, B2, AB...) 
    
    #Conjugation for Present Tense 
    
    present_first_singular = models.CharField(max_length=100) 
    present_second_singular = models.CharField(max_length= 100) 
    present_third_singular = models.CharField(max_length=100)
    present_first_plural = models.CharField(max_length=100) 
    present_second_plural = models.CharField(max_length=100)
    present_third_pluran = models.CharField(max_length=100)
    
    
    # Conjugation for aorist 
    
    aorist_first_singular = models.CharField(max_length=100) 
    aorist_second_singular = models.CharField(max_length=100)
    aorist_third_singular = models.CharField(max_length=100)
    aorist_first_plural = models.CharField(max_length=100)
    aorist_second_plural = models.CharField(max_length=100)
    aorist_third_plural = models.CharField(max_length=100)
    
    #Conjugation for Imperfect 
    
    imperfect_first_singular = models.CharField(max_length=100)
    imperfect_second_singular = models.CharField(max_length=100)
    imperfect_third_singular = models.CharField(max_length=100)
    imperfect_first_plural = models.CharField(max_length=100)
    imperfect_second_plural = models.CharField(max_length=100)
    imperfect_third_plural = models.CharField(max_length=100) 
    
    #Conjugation for Perfect 
    
    perfect_first_singular = models.CharField(max_length=100) 
    perfect_second_singular = models.CharField(max_length=100)
    perfect_third_singular = models.CharField(max_length=100) 
    perfect_first_plural = models.CharField(max_length=100) 
    perfect_second_plural = models.CharField(max_length=100)
    perfect_third_plural = models.CharField(max_length=100) 
    
    #Conjugation for Plusperfect 
    
    plusperfect_first_singular = models.CharField(max_length=100) 
    plusperfect_second_singular = models.CharField(max_length=100) 
    plusperfect_third_singular = models.CharField(max_length=100) 
    plusperfect_first_plural = models.CharField(max_length=100) 
    plusperfect_second_plural = models.CharField(max_length=100) 
    plusperfect_third_plural = models.CharField(max_length=100) 
    
    #Conjugation for Future 
    
    future_first_singular = models.CharField(max_length=100) 
    future_second_singular = models.CharField(max_length=100) 
    future_third_singular = models.CharField(max_length=100) 
    future_first_plural = models.CharField(max_length=100) 
    future_second_plural = models.CharField(max_length=100) 
    future_third_plural = models.CharField(max_length=100) 
    
    def __str__(self):
        return self.infinitive
    