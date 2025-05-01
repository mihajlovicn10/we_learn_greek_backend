from django.shortcuts import render
from .models import TransparentWord 
from django.db.models import Q 
from django.contrib.auth.decorators import login_required 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .api.serializers import TransparentWordSerializer


@login_required
def list_language(request): 
    languages = TransparentWord.objects.values_list("target_language", flat= True).distinct()
    return render(request, "transparent_languages.html", {"languages":languages}) 

@login_required 
def words_by_language(request, language): 
    search_query = request.GET.get('q') 
    
    if search_query: 
        words = TransparentWord.objects.filter(language= language, area__icontains = search_query) 
    else: 
        words = TransparentWord.objects.filter(language = language) 
        
class TransparentWordViewSet(viewsets.ModelViewSet):
    queryset = TransparentWord.objects.all()
    serializer_class = TransparentWordSerializer
    permission_classes = [AllowAny]  # Temporarily allow all access for testing
        
        