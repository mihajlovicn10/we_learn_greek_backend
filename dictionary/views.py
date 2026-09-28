from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from dictionary.api.serializers import BulkDeleteSerializer, DictionarySerializer
from django.db import IntegrityError, transaction
from we_learn_greek.search import GreekSearchFilter
from .models import Dictionary

DUPLICATE_WORD_ERROR = {"greek_word": ["You already have this word in your dictionary"]}


class DictionaryPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class DictionaryViewSet(viewsets.ModelViewSet):
    serializer_class = DictionarySerializer
    pagination_class = DictionaryPagination
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [GreekSearchFilter, filters.OrderingFilter]
    search_fields = ['greek_word', 'translation', 'pronounciation']
    ordering_fields = ['greek_word', 'date_added']
    ordering = ['-date_added']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # drf-yasg schema generation, no user
            return Dictionary.objects.none()
        return Dictionary.objects.filter(user=self.request.user)

    # The serializer's duplicate check can race with a concurrent request; the
    # (user, greek_word) unique constraint is the backstop.
    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError(DUPLICATE_WORD_ERROR)

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError:
            raise ValidationError(DUPLICATE_WORD_ERROR)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {"error": "You don't have permission to edit this word."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {"error": "You don't have permission to delete this word."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        serializer = BulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        deleted_count = Dictionary.objects.filter(
            id__in=serializer.validated_data['ids'],
            user=request.user,
        ).delete()[0]

        return Response({
            "message": f"Successfully deleted {deleted_count} words",
        })
