from django.contrib import admin
from .models import TransparentWord


@admin.register(TransparentWord)
class TransparentWordAdmin(admin.ModelAdmin):
    list_display = ("language", "greek_word", "language_word", "category")
    search_fields = ("language", "greek_word", "language_word", "category")
    list_filter = ("language", "category")