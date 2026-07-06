from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import VerbViewSet

router = DefaultRouter()
router.register('verbs', VerbViewSet, basename='verbs')

verb_list = VerbViewSet.as_view({'get': 'list', 'post': 'create'})
verb_detail = VerbViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = router.urls + [
    path('conjugator/', verb_list, name='conjugator-list'),
    path('conjugator/<int:pk>/', verb_detail, name='conjugator-detail'),
]
