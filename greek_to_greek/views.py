from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import GreekToGreek
from .api.serializers import GreekToGreekSerializer


@login_required
def greek_to_greek_dict(request):
    search_query = request.GET.get('q')
    if search_query:
        words = GreekToGreek.objects.filter(word__icontains=search_query).order_by("word")
    else:
        words = GreekToGreek.objects.all().order_by("word")
    return render(request, 'greek_to_greek_list.html', {"words": words})


@login_required
def greek_to_greek_detail(request, pk):
    word = get_object_or_404(GreekToGreek, pk=pk)
    return render(request, "greek_to_greek_detail.html", {"word": word})


class GreekToGreekViewSet(viewsets.ModelViewSet):
    queryset = GreekToGreek.objects.all()
    serializer_class = GreekToGreekSerializer
    permission_classes = [AllowAny]
