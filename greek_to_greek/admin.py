from django.contrib import admin
from .models import GreekToGreek


@admin.register(GreekToGreek)
class GreekToGreekAdmin(admin.ModelAdmin):
    list_display = ("word", "explanation")
    search_fields = ("word", "explanation")
    ordering = ("word",)
