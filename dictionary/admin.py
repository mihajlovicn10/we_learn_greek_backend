from django.contrib import admin
from .models import Dictionary 

@admin.register(Dictionary) 
class DictionaryAdmin(admin.ModelAdmin): 
    list_display = ("greek_word" , "pronounciation" , "translation") 
    search_fields = ("greek_word" , "pronounciation" , "translation") 
    ordering = ("greek_word",) 
    
    

