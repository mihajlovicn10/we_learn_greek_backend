from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from dictionary.models import Dictionary

User = get_user_model()


class DictionaryAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass",
            first_name="Test",
            last_name="User",
        )
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        self.dictionary_data = {
            "greek_word": "λόγος",
            "pronounciation": "logos",
            "translation": "word",
            "user": self.user,
        }
        self.dictionary_entry = Dictionary.objects.create(**self.dictionary_data)

        self.list_url = reverse("dictionary-list")
        self.detail_url = reverse("dictionary-detail", kwargs={"pk": self.dictionary_entry.pk})

    def test_list_dictionary_entries(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["greek_word"], "λόγος")

    def test_retrieve_dictionary_entry(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["greek_word"], "λόγος")

    def test_create_dictionary_entry(self):
        new_entry = {
            "greek_word": "φωνή",
            "pronounciation": "phone",
            "translation": "voice",
        }
        response = self.client.post(self.list_url, new_entry)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Dictionary.objects.count(), 2)
        self.assertEqual(response.data["greek_word"], "φωνή")

    def test_update_dictionary_entry(self):
        updated_data = {
            "greek_word": "λόγος",
            "pronounciation": "logos",
            "translation": "updated word",
        }
        response = self.client.put(self.detail_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dictionary_entry.refresh_from_db()
        self.assertEqual(self.dictionary_entry.translation, "updated word")

    def test_delete_dictionary_entry(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Dictionary.objects.count(), 0)

    def test_create_entry_unauthenticated(self):
        self.client.credentials()
        new_entry = {
            "greek_word": "φως",
            "pronounciation": "fos",
            "translation": "light",
        }
        response = self.client.post(self.list_url, new_entry)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bulk_delete(self):
        second = Dictionary.objects.create(
            greek_word="φωνή",
            pronounciation="phone",
            translation="voice",
            user=self.user,
        )
        response = self.client.post(
            reverse("dictionary-bulk-delete"),
            {"ids": [self.dictionary_entry.pk, second.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Dictionary.objects.count(), 0)
