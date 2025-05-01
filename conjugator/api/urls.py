from django.urls import path, include 
from .views import VerbListCreateAPIView, VerbDetailAPIView, VerbConjugationView
from rest_framework import filters

urlpatterns = [
    path('', VerbListCreateAPIView.as_view(), name = "verb_list_create"), 
    path('<int:pk>/', VerbDetailAPIView.as_view(), name= "verb_detail"), 
]
