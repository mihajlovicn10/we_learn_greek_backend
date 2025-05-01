from rest_framework import serializers 
from ..models import TransparentWord 

class TransparentWordSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = TransparentWord 
        fields = '__all__' 
        
        