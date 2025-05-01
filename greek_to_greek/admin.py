from django.contrib import admin
from .models import GreekToGreek 

class GreekToGreekAdmin(admin.ModelAdmin): 
    list_display = ("word",) 
    search_fields = ("word", "explanation") 
    ordering = ("word",)
