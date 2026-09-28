from rest_framework_simplejwt.views import TokenObtainPairView


# simplejwt names the login field after User.USERNAME_FIELD, which is already
# "email", so the stock serializer accepts {"email", "password"} as-is.
class EmailTokenObtainPairView(TokenObtainPairView):
    pass
