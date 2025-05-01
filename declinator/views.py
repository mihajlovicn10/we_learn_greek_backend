from django.shortcuts import render, get_object_or_404
from .models import Noun 
from django.db.models import Q 
from django.contrib.auth.decorators import login_required 
from rest_framework import viewsets, permissions, filters
from rest_framework.pagination import PageNumberPagination
from .api.serializers import NounSerializer
from rest_framework.permissions import AllowAny


@login_required
def list_noun(request): 
    nouns = Noun.objects.all().order_by('basic_noun') 
    return render(request, "noun_list.html") 

@login_required
def noun_detail(request, pk): 
    noun = get_object_or_404(Noun, pk=pk)  
    search_query = request.GET.get('q', None) 
    if search_query: 
        try: 
            noun = Noun.objects.get(name__icontains = search_query) 
        except: 
            noun = None 
    context = {
        'noun': noun, 
    }
    return render(request, 'noun_detail.html', {noun:noun}) 

class NounPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class NounViewSet(viewsets.ModelViewSet):
    queryset = Noun.objects.all()
    serializer_class = NounSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access temporarily
    pagination_class = NounPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nominative_singular', 'nominative_plural', 'gender']
    ordering_fields = ['nominative_singular', 'nominative_plural', 'gender']
    ordering = ['nominative_singular']

    def list(self, request, *args, **kwargs):
        print("Accessing nouns list")  # Debug print
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Noun.objects.all()
        nominative = self.request.query_params.get('nominative_singular', None)
        if nominative:
            queryset = queryset.filter(nominative_singular__icontains=nominative)
        return queryset 