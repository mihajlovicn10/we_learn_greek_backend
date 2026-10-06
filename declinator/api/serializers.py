from rest_framework import serializers 
from declinator.models import Noun 

class NounSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Noun
        fields = [
            'id',
            'tier',
            'basic_noun',
            'gender',
            'translations',
            'nominative_singular',
            'nominative_plural',
            'genitive_singular',
            'genitive_plural',
            'accusative_singular',
            'accusative_plural',
            'vocative_singular',
            'vocative_plural',
        ]
