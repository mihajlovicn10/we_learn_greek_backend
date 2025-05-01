from rest_framework import serializers 
from ..models import Verb 

class VerbSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Verb 
        fields = '__all__' 
    
    def validate_infinitive(self, value): 
        if not value: 
            raise serializers.ValidationError("Infinitive cannot be blank") 
        return value