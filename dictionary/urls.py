from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DictionaryViewSet

router = DefaultRouter()
router.register('dictionary', DictionaryViewSet, basename='dictionary')

dictionary_list = DictionaryViewSet.as_view({'get': 'list', 'post': 'create'})
dictionary_detail = DictionaryViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = router.urls + [
    path('dictionary-entries/', dictionary_list, name='dictionary_list_create'),
    path('dictionary-entries/<int:pk>/', dictionary_detail, name='dictionary_detail'),
]
