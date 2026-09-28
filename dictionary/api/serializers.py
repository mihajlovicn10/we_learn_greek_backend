import re

from rest_framework import serializers 
from ..models import Dictionary 
from ..validators import validate_greek

class DictionarySerializer(serializers.ModelSerializer): 
    # Redeclared field: model constraints are not inherited, so repeat max_length here.
    # Whitespace is normalised in to_internal_value before validate_greek runs.
    greek_word = serializers.CharField(
        max_length=Dictionary._meta.get_field('greek_word').max_length,
        validators=[validate_greek],
    )

    class Meta: 
        model = Dictionary 
        fields = ['id', 'greek_word', 'pronounciation', 'translation', 'date_added']
        read_only_fields = ['date_added', 'user']

    def to_internal_value(self, data):
        # Collapse runs of whitespace ("ο   λόγος" -> "ο λόγος") so validation and the
        # duplicate check see the stored form.
        if hasattr(data, 'get') and isinstance(data.get('greek_word'), str):
            data = data.copy()
            data['greek_word'] = re.sub(r'\s+', ' ', data['greek_word']).strip()
        return super().to_internal_value(data)

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


class BulkDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        max_length=1000,
        error_messages={'empty': 'No IDs provided'},
    )
