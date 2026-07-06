from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from dictionary.api.serializers import DictionarySerializer
from django.db.models import Q
from .models import Dictionary


class DictionaryPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class DictionaryViewSet(viewsets.ModelViewSet):
    serializer_class = DictionarySerializer
    pagination_class = DictionaryPagination
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['greek_word', 'translation']
    ordering_fields = ['greek_word', 'date_added']
    ordering = ['-date_added']

    def get_queryset(self):
        return Dictionary.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {"error": "No IDs provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deleted_count = Dictionary.objects.filter(
            id__in=ids,
            user=request.user,
        ).delete()[0]

        return Response({
            "message": f"Successfully deleted {deleted_count} words",
        })
