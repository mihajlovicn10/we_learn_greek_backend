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

    def test_create_noun(self):
        new_data = self.noun_data.copy()
        new_data["basic_noun"] = "ἄνθρωπος"
        new_data["nominative_singular"] = "ἄνθρωπος"
        response = self.client.post(self.api_url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Noun.objects.count(), 2)

    def test_retrieve_noun(self):
        response = self.client.get(f"{self.api_url}{self.noun.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["basic_noun"], self.noun_data["basic_noun"])

    def test_update_noun(self):
        updated_data = self.noun_data.copy()
        updated_data["basic_noun"] = "θεός"
        response = self.client.put(f"{self.api_url}{self.noun.id}/", updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.noun.refresh_from_db()
        self.assertEqual(self.noun.basic_noun, "θεός")

    def test_delete_noun(self):
        response = self.client.delete(f"{self.api_url}{self.noun.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Noun.objects.count(), 0)

    def test_create_noun_invalid_data(self):
        invalid_data = self.noun_data.copy()
        invalid_data.pop("basic_noun")
        response = self.client.post(self.api_url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
