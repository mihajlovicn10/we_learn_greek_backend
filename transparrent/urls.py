from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import TransparentWordViewSet

router = DefaultRouter()
router.register('transparent-words', TransparentWordViewSet, basename='transparent-words')

transparent_list = TransparentWordViewSet.as_view({'get': 'list', 'post': 'create'})
transparent_detail = TransparentWordViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = router.urls + [
    path('transparent-words-entries/', transparent_list, name='transparent_word_list_create'),
    path('transparent-words-entries/<int:pk>/', transparent_detail, name='transparent_word_detail'),
    path(
        'transparent-words/language/<str:language>/',
        transparent_list,
        name='transparent_word_by_language',
    ),
]
