from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import TransparentWord


class TransparentWordAPITestCase(APITestCase):
    def setUp(self):
        self.transparent_word = TransparentWord.objects.create(
            language="en",
            greek_word="πρόβλημα",
            language_word="problem",
            pronunciation="PROV-lee-mah",
            etymology="From Greek πρόβλημα",
            category="Science",
        )

        self.list_url = reverse("transparent-words-list")
        self.detail_url = reverse("transparent-words-detail", kwargs={"pk": self.transparent_word.pk})
        self.language_url = reverse("transparent_word_by_language", kwargs={"language": "en"})

    def test_create_transparent_word(self):
        data = {
            "language": "fr",
            "greek_word": "φιλοσοφία",
            "language_word": "philosophie",
            "category": "Philosophy",
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TransparentWord.objects.count(), 2)

    def test_list_transparent_words(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_transparent_word(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["greek_word"], "πρόβλημα")

    def test_update_transparent_word(self):
        updated_data = {
            "language": "en",
            "greek_word": "πρόβλημα",
            "language_word": "problem",
            "category": "Education",
        }
        response = self.client.put(self.detail_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transparent_word.refresh_from_db()
        self.assertEqual(self.transparent_word.category, "Education")

    def test_delete_transparent_word(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TransparentWord.objects.count(), 0)

    def test_filter_by_language_path(self):
        TransparentWord.objects.create(
            language="fr",
            greek_word="φιλοσοφία",
            language_word="philosophie",
            category="Philosophy",
        )
        response = self.client.get(self.language_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["language"], "en")

    def test_filter_by_language_query_param(self):
        response = self.client.get(self.list_url, {"language": "en"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_by_language_action(self):
        response = self.client.get("/api/transparent-words/by-language/en/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
