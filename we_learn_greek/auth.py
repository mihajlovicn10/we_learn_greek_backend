from django.contrib.auth import get_user_model
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.utils import get_md5_hash_password
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView


# simplejwt names the login field after User.USERNAME_FIELD, which is already
# "email", so the stock serializer accepts {"email", "password"} as-is.
class EmailTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


class RevocationAwareTokenRefreshSerializer(TokenRefreshSerializer):
    """simplejwt only enforces CHECK_REVOKE_TOKEN when authenticating an access token;
    also refuse to refresh a token issued before the user's password changed."""

    def validate(self, attrs):
        refresh = self.token_class(attrs['refresh'])
        if api_settings.CHECK_REVOKE_TOKEN:
            user = get_user_model().objects.filter(
                **{api_settings.USER_ID_FIELD: refresh.payload.get(api_settings.USER_ID_CLAIM)}
            ).first()
            if user is None or refresh.payload.get(api_settings.REVOKE_TOKEN_CLAIM) != get_md5_hash_password(user.password):
                raise AuthenticationFailed("The user's password has been changed.", code='password_changed')
        return super().validate(attrs)


# Returns {"access", "refresh"}: refresh tokens rotate, and the one sent in is blacklisted.
class ThrottledTokenRefreshView(TokenRefreshView):
    serializer_class = RevocationAwareTokenRefreshSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'token'


# Body {"refresh"}: blacklists that refresh token. Works without a valid access token,
# so a client whose access token has already expired can still log out.
class LogoutView(TokenBlacklistView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'token'
