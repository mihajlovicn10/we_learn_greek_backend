from rest_framework import serializers 
from ..models import GreekToGreek 

class GreekToGreekSerializer(serializers.ModelSerializer): 
    
    class Meta: 
        model = GreekToGreek 
        exclude = ['content_id']  # internal: the item id within its content file
        
        
    