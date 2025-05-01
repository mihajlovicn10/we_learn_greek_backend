from rest_framework import serializers 
from ..models import GreekToGreek 

class GreekToGreekSerializer(serializers.ModelSerializer): 
    
    class Meta: 
        model = GreekToGreek 
        fields = '__all__' 
        
        
    