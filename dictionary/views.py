from django.shortcuts import render, redirect
from .models import Dictionary
from django.contrib import messages
from django.contrib.auth.decorators import login_required 
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from dictionary.api.serializers import DictionarySerializer
from django.db.models import Q
from rest_framework.decorators import action

@login_required 
def dictionary_view(request): 
    user = request.user 
    word = Dictionary.objects.filter(user=user) 
    return render(request, "dictionary/dictionary.html", {"word": word}) 

@login_required
def add_word(request):
    if request.method == 'POST': 
        greek_word = request.POST.get('greek_word').strip() 
        pronounciation = request.POST.get('pronounciation', '').strip()
        translation = request.POST.get('translation').strip()
        
        if not greek_word: 
            messages.error(request, "Greek word must not be empty.")
            return redirect('add_word') 
        
        if not pronounciation: 
            messages.error(request, "Pronounciation must not be empty.")
            return redirect("add_word") 
        
        if not translation:
            messages.error(request, "Translation must not be empty.") 
            return redirect('add_word')  
        
        if Dictionary.objects.filter(user = request.user , greek_word = greek_word).exists(): 
            messages.error(request, 'This word is already in the dictionary')
        else: 
            Dictionary.objects.create(
                greek_word=greek_word,
                pronounciation=pronounciation,
                translation=translation,
                user=request.user,
            )
            messages.success(request, "A word has been added successfully!") 
        return redirect('add_word') 
    
    return render(request, "dictionary/add_word.html")


@login_required
def list_words(request): 
    words = Dictionary.objects.filter(user= request.user).order_by('greek_word') 
    return render(request, 'dictionary/list_words.html',{'words': words})  

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
        # Check if the user owns this word
        if instance.user != request.user:
            return Response(
                {"error": "You don't have permission to edit this word."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if the user owns this word
        if instance.user != request.user:
            return Response(
                {"error": "You don't have permission to delete this word."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {"error": "No IDs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only delete words owned by the user
        deleted_count = Dictionary.objects.filter(
            id__in=ids,
            user=request.user
        ).delete()[0]

        return Response({
            "message": f"Successfully deleted {deleted_count} words"
        })  