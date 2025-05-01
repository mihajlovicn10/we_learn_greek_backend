from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import NounViewSet

router = DefaultRouter()
router.register('nouns', NounViewSet, basename='nouns')

urlpatterns = router.urls 