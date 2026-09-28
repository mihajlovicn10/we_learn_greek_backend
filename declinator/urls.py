from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NounViewSet

router = DefaultRouter()
router.register('nouns', NounViewSet, basename='nouns')

noun_list = NounViewSet.as_view({'get': 'list'})
noun_detail = NounViewSet.as_view({'get': 'retrieve'})

urlpatterns = router.urls + [
    path('declinator/', noun_list, name='declinator-list'),
    path('declinator/<int:pk>/', noun_detail, name='declinator-detail'),
]
