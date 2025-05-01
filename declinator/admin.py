from django.contrib import admin
from .models import Noun 

@admin.register(Noun) 
class NounAdmin(admin.ModelAdmin): 
    list_display = (
        "basic_noun", 
        "nominative_singular", 
        "genitive_singular", 
        "accusative_singular", 
        "vocative_singular", 
        "nominative_plural", 
        "genitive_plural", 
        "accusative_plural", 
        "vocative_plural", 
    )

    search_fields = ("basic_noun", "gender") 
    ordering = ("basic_noun",) 
    
    
