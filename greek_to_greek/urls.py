from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import GreekToGreekViewSet

router = DefaultRouter()
router.register('greek-to-greek', GreekToGreekViewSet, basename='greek-to-greek')

greek_list = GreekToGreekViewSet.as_view({'get': 'list', 'post': 'create'})
greek_detail = GreekToGreekViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = router.urls + [
    path('greek-to-greek-entries/', greek_list, name='greek_to_greek_list_create'),
    path('greek-to-greek-entries/<int:pk>/', greek_detail, name='greek_to_greek_detail'),
]
