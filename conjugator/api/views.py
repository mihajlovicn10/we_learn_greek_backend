from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly 
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Verb 
from .serializers import VerbSerializer, ConjugationSerializer

class VerbListCreateAPIView(ListCreateAPIView):
    queryset = Verb.objects.all() 
    serializer_class = VerbSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['infinitive']
    filterset_fields = ['verb_type']
    
class VerbDetailAPIView(RetrieveUpdateDestroyAPIView): 
    queryset = Verb.objects.all() 
    serializer_class = VerbSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 

class VerbConjugationView(RetrieveAPIView):
    queryset = Verb.objects.all()
    serializer_class = ConjugationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    