from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from .models import Noun
from .api.serializers import NounSerializer


@login_required
def list_noun(request):
    nouns = Noun.objects.all().order_by('basic_noun')
    return render(request, "noun_list.html", {"nouns": nouns})


@login_required
def noun_detail(request, pk):
    noun = get_object_or_404(Noun, pk=pk)
    search_query = request.GET.get('q')
    if search_query:
        noun = Noun.objects.filter(basic_noun__icontains=search_query).first() or noun
    return render(request, 'noun_detail.html', {'noun': noun})


class NounPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class NounViewSet(viewsets.ModelViewSet):
    queryset = Noun.objects.all()
    serializer_class = NounSerializer
    permission_classes = [AllowAny]
    pagination_class = NounPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nominative_singular', 'nominative_plural', 'gender', 'basic_noun']
    ordering_fields = ['nominative_singular', 'nominative_plural', 'gender', 'basic_noun']
    ordering = ['nominative_singular']

    def get_queryset(self):
        queryset = Noun.objects.all()
        nominative = self.request.query_params.get('nominative_singular')
        if nominative:
            queryset = queryset.filter(nominative_singular__icontains=nominative)
        return queryset
