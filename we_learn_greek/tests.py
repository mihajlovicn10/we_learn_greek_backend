from rest_framework.test import APITestCase
from rest_framework import status
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
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

    # Pin CORS to an explicit allow-list, as in production. Otherwise the result depends on
    # DEBUG: with DEBUG on every origin is allowed, but CI runs with DEBUG off.
    @override_settings(CORS_ALLOWED_ORIGINS=["https://app.example.com"], CORS_ALLOW_ALL_ORIGINS=False)
    def test_throttled_response_exposes_retry_after_cross_origin(self):
        # Regression: without Access-Control-Expose-Headers the frontend can't read Retry-After.
        payload = {"email": "nobody@example.com", "password": "wrongpassword"}
        origin = {"HTTP_ORIGIN": "https://app.example.com"}
        for _ in range(10):
            self.client.post(self.login_url, payload, **origin)
        response = self.client.post(self.login_url, payload, **origin)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertTrue(response["Retry-After"].isdigit())
        self.assertIn("Access-Control-Allow-Origin", response)  # it is a CORS response
        self.assertIn("retry-after", response["Access-Control-Expose-Headers"].lower())

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


@PLAIN_STATIC_STORAGE
class AdminHardeningTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_admin_uses_throttled_site(self):
        from django.contrib import admin
        from .admin_site import ThrottledAdminSite
        self.assertIsInstance(admin.site, ThrottledAdminSite)

    def test_admin_login_is_throttled(self):
        url = reverse("admin:login")
        payload = {"username": "nobody@example.com", "password": "wrong"}
        statuses = [self.client.post(url, payload).status_code for _ in range(6)]
        self.assertEqual(statuses[:5], [200] * 5)  # failed login re-renders the form
        self.assertEqual(statuses[5], 429)
        self.assertEqual(self.client.get(url).status_code, 200)  # viewing the form is not limited

    def _reload_urls(self):
        import importlib
        from django.urls import clear_url_caches
        from . import urls
        clear_url_caches()
        importlib.reload(urls)

    def test_admin_url_and_toggle(self):
        try:
            with override_settings(ADMIN_URL="hidden-admin/"):
                self._reload_urls()
                self.assertEqual(reverse("admin:index"), "/hidden-admin/")
            with override_settings(ADMIN_ENABLED=False):
                self._reload_urls()
                self.assertEqual(self.client.get("/admin/").status_code, 404)
        finally:
            self._reload_urls()


class GreekSearchHelperTests(SimpleTestCase):
    """Unit tests for we_learn_greek.search (mirrored in the frontend's src/utils/greek.js)."""

    def test_normalize_strips_accents_case_and_final_sigma(self):
        from .search import normalize_greek

        self.assertEqual(normalize_greek("Άνθρωπος"), "ανθρωποσ")
        self.assertEqual(normalize_greek("ΪΫ"), "ιυ")

    def test_transliterate_is_phonetic(self):
        from .search import transliterate

        self.assertEqual(transliterate("άνθρωπος"), "anthropos")
        self.assertEqual(transliterate("είμαι"), "ime")
        self.assertEqual(transliterate("ευχαριστώ"), "efharisto")
        self.assertEqual(transliterate("αύριο"), "avrio")
        self.assertEqual(transliterate("μπύρα"), "bira")

    def test_matches(self):
        from .search import matches

        cases = [
            ("άνθρωπος", "ανθρωπος", True),  # accents optional
            ("άνθρωπος", "ΑΝΘΡ", True),  # case-insensitive prefix
            ("άνθρωπος", "anthropos", True),  # Latin input
            ("φιλοσοφία", "philosophia", True),  # spelling variants
            ("μπύρα", "mpyra", True),
            ("Καλημέρα", "kalimera", True),
            ("democracy", "Democ", True),  # Latin fields still match plainly
            ("σπίτι", "ανθρωπος", False),
            ("σπίτι", "anthropos", False),
            ("", "spiti", False),
            ("σπίτι", "", True),  # empty query matches everything
        ]
        for value, query, expected in cases:
            with self.subTest(value=value, query=query):
                self.assertEqual(matches(value, query), expected)
