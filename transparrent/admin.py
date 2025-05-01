from django.contrib import admin
from .models import TransparentWord 

class TransparentWordAdmin(admin.ModelAdmin): 
    list_display = ("target_language" , "word" , "root_word", "area") 
    search_fields = ("target_language" , "word" , "root_word", "area")
    list_filter = ("target_language", "area")
    