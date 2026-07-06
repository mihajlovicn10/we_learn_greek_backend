from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import TransparentWord
from .api.serializers import TransparentWordSerializer


@login_required
def list_language(request):
    languages = TransparentWord.objects.values_list("language", flat=True).distinct()
    return render(request, "transparent_languages.html", {"languages": languages})


@login_required
def words_by_language(request, language):
    search_query = request.GET.get('q')
    words = TransparentWord.objects.filter(language=language)
    if search_query:
        words = words.filter(
            greek_word__icontains=search_query
        ) | words.filter(language_word__icontains=search_query)
    return render(request, "transparent_words.html", {"words": words, "language": language})


class TransparentWordViewSet(viewsets.ModelViewSet):
    queryset = TransparentWord.objects.all()
    serializer_class = TransparentWordSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = TransparentWord.objects.all()
        language = self.kwargs.get('language') or self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
        return queryset

    @action(detail=False, methods=['get'], url_path='by-language/(?P<language>[^/.]+)')
    def by_language(self, request, language=None):
        words = TransparentWord.objects.filter(language=language)
        serializer = self.get_serializer(words, many=True)
        return Response(serializer.data)
