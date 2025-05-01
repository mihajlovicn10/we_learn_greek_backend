from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import DictionaryViewSet

router = DefaultRouter()
router.register('dictionary', DictionaryViewSet, basename='dictionary')

urlpatterns = router.urls 