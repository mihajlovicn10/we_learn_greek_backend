from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly 
from ..models import Noun 
from .serializers import NounSerializer 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

class NounListCreateAPIView(ListCreateAPIView): 
    queryset = Noun.objects.all() 
    serializer_class = NounSerializer 
    # Comment out permission_classes temporarily for testing
    # permission_classes = [IsAuthenticatedOrReadOnly]
    
class NounDetailAPIView(RetrieveUpdateDestroyAPIView): 
    queryset = Noun.objects.all() 
    serializer_class = NounSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 

class NounViewSet(viewsets.ModelViewSet):
    queryset = Noun.objects.all()
    serializer_class = NounSerializer
    permission_classes = [AllowAny]  # Temporarily allow all access
    
    def list(self, request, *args, **kwargs):
        print("Accessing nouns list view")  # Debug print
        return super().list(request, *args, **kwargs)
    
    
