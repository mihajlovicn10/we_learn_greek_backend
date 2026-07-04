from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Accept `email` instead of `username` for JWT login."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        email_field = self.fields.pop(self.username_field)
        email_field.label = 'Email'
        self.fields['email'] = email_field

    def validate(self, attrs):
        attrs[self.username_field] = attrs.get('email', '')
        return super().validate(attrs)


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
