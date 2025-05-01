from django.contrib import admin
from .models import Verb 

@admin.register(Verb)
class VerbAdmin(admin.ModelAdmin): 
    list_display = (
        "infinitive", 
        "verb_type", 
        "present_first_singular" , 
        "present_second_singular" , 
        "present_third_singular" , 
        "present_first_plural" , 
        "present_second_plural" , 
        "present_third_pluran", 
        "aorist_first_singular", 
        "aorist_second_singular", 
        "aorist_third_singular", 
        "aorist_first_plural", 
        "aorist_second_plural", 
        "aorist_third_plural", 
        "imperfect_first_singular", 
        "imperfect_second_singular", 
        "imperfect_third_singular", 
        "imperfect_first_plural", 
        "imperfect_second_plural", 
        "imperfect_third_plural", 
        "perfect_first_singular", 
        "perfect_second_singular", 
        "perfect_third_singular", 
        "perfect_first_plural", 
        "perfect_second_plural", 
        "perfect_third_plural", 
        "plusperfect_first_singular", 
        "plusperfect_second_singular", 
        "plusperfect_third_singular", 
        "plusperfect_first_plural", 
        "plusperfect_second_plural", 
        "plusperfect_third_plural", 
        "future_first_singular", 
        "future_second_singular", 
        "future_third_singular", 
        "future_first_plural", 
        "future_second_plural", 
        "future_third_plural"
        
    )
    
    search_fields = ("infinitive" , "verb_type")
    ordering = ("infinitive",) 


