from django.urls import path
from .views import NounListCreateAPIView, NounDetailAPIView 


urlpatterns = [
    path('', NounListCreateAPIView.as_view(), name= 'noun_list_create'), 
    path('<int:pk>/', NounDetailAPIView.as_view(), name= "noun_detail"), 
]
