from rest_framework.test import APITestCase
from rest_framework import status
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from .models import User


class UserAuthenticationTests(APITestCase):
    def setUp(self):
        cache.clear()  # throttle counters live in the cache
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.valid_user_data = {
            "email": "testuser@example.com",
            "password": "securepassword123",
            "first_name": "Test",
            "last_name": "User",
        }
        self.invalid_user_data = {
            "email": "",
            "password": "short",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_register_valid_user(self):
        response = self.client.post(self.register_url, self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTrue(User.objects.filter(email=self.valid_user_data["email"]).exists())

    def test_register_multiple_users(self):
        first = self.client.post(self.register_url, self.valid_user_data)
        second = self.client.post(self.register_url, {
            **self.valid_user_data,
            "email": "second@example.com",
        })
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

    def test_register_duplicate_email(self):
        self.client.post(self.register_url, self.valid_user_data)
        response = self.client.post(self.register_url, self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_duplicate_email_different_case(self):
        self.client.post(self.register_url, self.valid_user_data)
        response = self.client.post(self.register_url, {
            **self.valid_user_data,
            "email": "TestUser@Example.com",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_stores_lowercased_email(self):
        response = self.client.post(self.register_url, {
            **self.valid_user_data,
            "email": "Mixed.Case@Example.COM",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "mixed.case@example.com")

    def test_register_without_names(self):
        response = self.client.post(self.register_url, {
            "email": self.valid_user_data["email"],
            "password": self.valid_user_data["password"],
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_weak_passwords_rejected(self):
        for password in ["short", "12345678901", "password", "testuser@example.com"]:
            response = self.client.post(self.register_url, {
                **self.valid_user_data,
                "password": password,
            })
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, password)
            self.assertIn("password", response.data, password)
        self.assertEqual(User.objects.count(), 0)

    def test_login_email_is_case_insensitive(self):
        User.objects.create_user(**self.valid_user_data)
        for url in [self.login_url, reverse("token_obtain_pair")]:
            response = self.client.post(url, {
                "email": "TESTUSER@example.com",
                "password": self.valid_user_data["password"],
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK, url)

    def test_auth_endpoints_are_throttled(self):
        payload = {"email": "nobody@example.com", "password": "wrongpassword"}
        statuses = [self.client.post(self.login_url, payload).status_code for _ in range(11)]
        self.assertEqual(statuses[:10], [status.HTTP_401_UNAUTHORIZED] * 10)
        self.assertEqual(statuses[10], status.HTTP_429_TOO_MANY_REQUESTS)

    def test_register_invalid_user(self):
        response = self.client.post(self.register_url, self.invalid_user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(User.objects.filter(email=self.invalid_user_data["email"]).count(), 0)

    def test_login_valid_user(self):
        User.objects.create_user(**self.valid_user_data)
        response = self.client.post(self.login_url, {
            "email": self.valid_user_data["email"],
            "password": self.valid_user_data["password"],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("access", response.data)

    def test_token_endpoint_returns_token_pair(self):
        User.objects.create_user(**self.valid_user_data)
        response = self.client.post(reverse("token_obtain_pair"), {
            "email": self.valid_user_data["email"],
            "password": self.valid_user_data["password"],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_user(self):
        response = self.client.post(self.login_url, {
            "email": self.valid_user_data["email"],
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_login_disabled_user(self):
        User.objects.create_user(**self.valid_user_data, is_active=False)
        response = self.client.post(self.login_url, {
            "email": self.valid_user_data["email"],
            "password": self.valid_user_data["password"],
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="supersafepassword123",
            first_name="Admin",
            last_name="User",
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)


# The manifest storage used in production needs collectstatic to have run.
PLAIN_STATIC_STORAGE = override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})


@PLAIN_STATIC_STORAGE
class ApiDocsTests(APITestCase):
    def test_docs_pages_render(self):
        for url in ["/swagger/", "/redoc/", "/swagger/?format=openapi"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, url)


class TokenLifecycleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.password = "correct-horse-battery"
        self.user = User.objects.create_user(email="jwt@example.com", password=self.password)
        response = self.client.post(reverse("login"), {"email": "jwt@example.com", "password": self.password})
        self.access = response.data["access"]
        self.refresh = response.data["refresh"]

    def _refresh(self, token):
        return self.client.post(reverse("token_refresh"), {"refresh": token})

    def _get_dictionary(self, access):
        return self.client.get(reverse("dictionary-list"), HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_refresh_rotates_and_old_token_is_rejected(self):
        first = self._refresh(self.refresh)
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", first.data)
        self.assertNotEqual(first.data["refresh"], self.refresh)

        reused = self._refresh(self.refresh)
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

        second = self._refresh(first.data["refresh"])
        self.assertEqual(second.status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh_token(self):
        response = self.client.post(reverse("logout"), {"refresh": self.refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._refresh(self.refresh).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_token(self):
        response = self.client.post(reverse("logout"), {"refresh": "not-a-token"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change_revokes_existing_tokens(self):
        self.assertEqual(self._get_dictionary(self.access).status_code, status.HTTP_200_OK)
        self.user.set_password("another-strong-password")
        self.user.save()
        self.assertEqual(self._get_dictionary(self.access).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self._refresh(self.refresh).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tokens_from_token_endpoint_also_work(self):
        response = self.client.post(reverse("token_obtain_pair"), {"email": "jwt@example.com", "password": self.password})
        self.assertEqual(self._get_dictionary(response.data["access"]).status_code, status.HTTP_200_OK)
        self.assertEqual(self._refresh(response.data["refresh"]).status_code, status.HTTP_200_OK)
