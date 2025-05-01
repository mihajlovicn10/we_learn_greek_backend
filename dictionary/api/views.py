from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.authentication import TokenAuthentication 
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from ..models import Dictionary 
from .serializers import DictionarySerializer 

class DictionaryListCreateAPIView(ListCreateAPIView): 
    queryset = Dictionary.objects.all() 
    serializer_class = DictionarySerializer 
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly] 
    
class DictionaryDetailAPIView(RetrieveUpdateDestroyAPIView): 
    queryset = Dictionary.objects.all() 
    serializer_class = DictionarySerializer
    authentication_classes = [TokenAuthentication] 
    permission_classes = [IsAuthenticatedOrReadOnly]  
    
    
    