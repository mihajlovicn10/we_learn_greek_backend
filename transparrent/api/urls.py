from django.urls import path 
from .views import TransparentWordListCreateAPIView, TransparentWordDetailAPIView 

urlpatterns = [
    path('', TransparentWordListCreateAPIView.as_view(), name='transparent_word_list_create'), 
    path('<int:pk>/', TransparentWordDetailAPIView.as_view(), name='transparent_word_detail'),
    path('language/<str:language>/', TransparentWordListCreateAPIView.as_view(), name='transparent_word_by_language'),
]
