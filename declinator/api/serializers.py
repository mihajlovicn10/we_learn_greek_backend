from rest_framework import serializers 
from declinator.models import Noun 

class NounSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Noun
        fields = [
            'id',
            'basic_noun',
            'gender',
            'nominative_singular',
            'nominative_plural',
            'genitive_singular',
            'genitive_plural',
            'accusative_singular',
            'accusative_plural',
            'vocative_singular',
            'vocative_plural',
        ] 
        
    def to_representation(self, instance):
        # Add debug print
        print("Serializing fields:", self.Meta.fields)
        return super().to_representation(instance)
        
        