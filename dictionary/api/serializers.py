from rest_framework import serializers 
from ..models import Dictionary 
from django.core.validators import RegexValidator

class DictionarySerializer(serializers.ModelSerializer): 
    greek_word = serializers.CharField(
        validators=[
            RegexValidator(
                regex='^[α-ωΑ-Ωίϊΐόάέύϋΰήώ\s]+$',
                message='Only Greek characters are allowed'
            )
        ]
    )

    class Meta: 
        model = Dictionary 
        fields = ['id', 'greek_word', 'pronounciation', 'translation', 'date_added']
        read_only_fields = ['date_added', 'user']

    def validate_greek_word(self, value):
        # Check for minimum length
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Word must be at least 2 characters long"
            )
        
        # Check if word already exists for this user
        user = self.context['request'].user
        if Dictionary.objects.filter(
            user=user,
            greek_word__iexact=value
        ).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError(
                "You already have this word in your dictionary"
            )
        
        return value.strip()

    def validate_pronounciation(self, value):
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Pronunciation must be at least 2 characters long"
            )
        return value.strip()

    def validate_translation(self, value):
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError(
                "Translation is required"
            )
        return value.strip()

    def update(self, instance, validated_data):
        # Add any specific update logic here if needed
        return super().update(instance, validated_data) 
            
