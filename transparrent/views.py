from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny

from we_learn_greek.search import GreekSearchFilter
from we_learn_greek.throttling import CONTENT_THROTTLES

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


class TransparentWordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TransparentWord.objects.all()
    serializer_class = TransparentWordSerializer
    permission_classes = [AllowAny]
    throttle_classes = CONTENT_THROTTLES
    filter_backends = [GreekSearchFilter]
    search_fields = ['greek_word', 'language_word']

    def get_queryset(self):
        queryset = TransparentWord.objects.all()
        language = self.kwargs.get('language') or self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)
        tier = self.request.query_params.get('tier')
        if tier is not None:
            if not tier.isdigit():
                raise ValidationError({'tier': ['Must be a whole number, e.g. ?tier=1.']})
            queryset = queryset.filter(tier=int(tier))
        return queryset

    # Same filtering and pagination as the list; the frontend sends ?search, ?category,
    # ?page and ?page_size here and handles the paginated {count, results} shape.
    @action(detail=False, methods=['get'], url_path='by-language/(?P<language>[^/.]+)')
    def by_language(self, request, language=None):
        return self.list(request)
