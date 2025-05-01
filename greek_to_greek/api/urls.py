from django.urls import path 
from .views import GreekToGreekListCreateAPIView, GreekToGreekDetailAPIView 

urlpatterns = [
    path('', GreekToGreekListCreateAPIView.as_view(), name= "greek_to_greek_list_create"), 
    path('<int:pk>/', GreekToGreekDetailAPIView.as_view(), name= "greek_to_greek_detail"), 
]
