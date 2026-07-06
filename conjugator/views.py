from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Verb
from .api.serializers import VerbSerializer, ConjugationSerializer


@login_required
def list_verbs(request):
    verbs = Verb.objects.all().order_by("infinitive")
    return render(request, "verbs_list.html", {"verbs": verbs})


@login_required
def verb_detail(request, pk):
    verb = get_object_or_404(Verb, pk=pk)
    search_query = request.GET.get('q')
    if search_query:
        verb = Verb.objects.filter(infinitive__icontains=search_query).first()
    return render(request, 'verb_detail.html', {'verb': verb})


class VerbViewSet(viewsets.ModelViewSet):
    queryset = Verb.objects.all()
    serializer_class = VerbSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['infinitive']
    filterset_fields = ['verb_type']

    @action(detail=True, methods=['get'])
    def conjugation(self, request, pk=None):
        verb = self.get_object()
        serializer = ConjugationSerializer(verb)
        return Response(serializer.data)
