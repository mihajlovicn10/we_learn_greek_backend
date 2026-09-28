from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Noun

User = get_user_model()


class NounAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.noun_data = {
            "basic_noun": "λόγος",
            "nominative_singular": "λόγος",
            "genitive_singular": "λόγου",
            "accusative_singular": "λόγον",
            "vocative_singular": "λόγε",
            "nominative_plural": "λόγοι",
            "genitive_plural": "λόγων",
            "accusative_plural": "λόγους",
            "vocative_plural": "λόγοι",
            "gender": "masculine",
        }

        self.noun = Noun.objects.create(**self.noun_data)
        self.api_url = "/api/declinator/"

    def test_write_methods_not_allowed(self):
        detail_urls = [f"{self.api_url}{self.noun.id}/", f"/api/nouns/{self.noun.id}/"]
        for url in [self.api_url, "/api/nouns/"]:
            response = self.client.post(url, self.noun_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, url)
        for url in detail_urls:
            for method in (self.client.put, self.client.patch, self.client.delete):
                response = method(url, self.noun_data, format="json")
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, url)
        self.noun.refresh_from_db()
        self.assertEqual(self.noun.basic_noun, "λόγος")
        self.assertEqual(Noun.objects.count(), 1)

    def test_retrieve_noun(self):
        response = self.client.get(f"{self.api_url}{self.noun.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["basic_noun"], self.noun_data["basic_noun"])
