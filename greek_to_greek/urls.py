from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GreekToGreekViewSet

router = DefaultRouter()
router.register('greek-to-greek', GreekToGreekViewSet, basename='greek-to-greek')

urlpatterns = router.urls 