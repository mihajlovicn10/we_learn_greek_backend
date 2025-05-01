from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly 
from rest_framework.authentication import TokenAuthentication 
from ..models import TransparentWord 
from .serializers import TransparentWordSerializer

class TransparentWordListCreateAPIView(ListCreateAPIView): 
    serializer_class = TransparentWordSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 
    authentication_classes = [TokenAuthentication] 
    
    def get_queryset(self):
        queryset = TransparentWord.objects.all()
        
        # Check for language in URL kwargs (from path parameter)
        language_from_url = self.kwargs.get('language')
        if language_from_url:
            return queryset.filter(language=language_from_url)
            
        # Check for language in query parameters
        language_from_query = self.request.query_params.get('language')
        if language_from_query:
            return queryset.filter(language=language_from_query)
            
        return queryset
    
    
class TransparentWordDetailAPIView(RetrieveUpdateDestroyAPIView): 
    queryset = TransparentWord.objects.all()
    serializer_class = TransparentWordSerializer 
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [TokenAuthentication] 
    
    