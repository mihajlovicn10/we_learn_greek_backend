from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User


class UserAuthenticationTests(APITestCase):
    def setUp(self):
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
