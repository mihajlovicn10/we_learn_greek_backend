from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TransparentWordViewSet

router = DefaultRouter()
router.register('transparent-words', TransparentWordViewSet, basename='transparent-words')

urlpatterns = router.urls