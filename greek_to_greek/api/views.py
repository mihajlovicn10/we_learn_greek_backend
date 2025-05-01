from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView 
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication 
from ..models import GreekToGreek 
from .serializers import GreekToGreekSerializer 

class GreekToGreekListCreateAPIView(ListCreateAPIView): 
    queryset = GreekToGreek.objects.all() 
    serializer_class = GreekToGreekSerializer 
    authentication_classes = [TokenAuthentication] 
    permission_classes = [IsAuthenticatedOrReadOnly]  
    
class GreekToGreekDetailAPIView(RetrieveUpdateDestroyAPIView): 
    queryset = GreekToGreek.objects.all() 
    serializer_class = GreekToGreekSerializer 
    authentication_classes = [TokenAuthentication] 
    permission_classes = [IsAuthenticatedOrReadOnly] 
    
    