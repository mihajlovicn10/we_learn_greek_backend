from rest_framework import serializers 
from ..models import TransparentWord 

class TransparentWordSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = TransparentWord 
        exclude = ['content_id']  # internal: the item id within its content file
        
        