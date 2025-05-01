from django.shortcuts import render, get_object_or_404
from .models import Verb 
from django.db.models import Q 
from django.contrib.auth.decorators import login_required 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .api.serializers import VerbSerializer

@login_required
def list_verbs(request): 
    verbs = Verb.objects.all().order_by("infinitive") 
    return render(request, "verbs_list.html") 

@login_required
def verb_detail(request, pk): 
    verb = get_object_or_404(Verb, pk=pk) 
    search_query = request.GET.get('q', None) 
    if search_query: 
        try: 
            verb = Verb.objects.get(name__icontains= search_query) 
        except: 
            verb = None 
    context = {
        'verb' : verb, 
    }
    return render(request, 'verb_detail.html', {verb:verb}) 

class VerbViewSet(viewsets.ModelViewSet):
    queryset = Verb.objects.all()
    serializer_class = VerbSerializer
    permission_classes = [AllowAny]  # Temporarily allow all access for testing 