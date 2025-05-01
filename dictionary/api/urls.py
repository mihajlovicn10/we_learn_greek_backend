from django.urls import path 
from .views import DictionaryListCreateAPIView, DictionaryDetailAPIView 



urlpatterns = [
    path('', DictionaryListCreateAPIView.as_view(), name = "dictionary_list_create"), 
    path('<int:pk>/', DictionaryDetailAPIView. as_view(), name = "dictionary_detail"), 
]

