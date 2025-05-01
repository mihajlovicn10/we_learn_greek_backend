from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import VerbViewSet

router = DefaultRouter()
router.register('verbs', VerbViewSet, basename='verbs')

urlpatterns = router.urls 