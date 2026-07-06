from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from greek_to_greek.models import GreekToGreek


class GreekToGreekAPITestCase(APITestCase):
    def setUp(self):
        self.greek_to_greek = GreekToGreek.objects.create(
            word="λόγος",
            explanation="Speech or reason",
        )
        self.list_url = reverse("greek-to-greek-list")
        self.detail_url = reverse("greek-to-greek-detail", kwargs={"pk": self.greek_to_greek.pk})

    def test_create_greek_to_greek_entry(self):
        data = {"word": "φως", "explanation": "Light"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GreekToGreek.objects.count(), 2)

    def test_list_greek_to_greek_entries(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_greek_to_greek_entry(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["word"], "λόγος")

    def test_update_greek_to_greek_entry(self):
        updated_data = {"word": "λόγος", "explanation": "Updated explanation"}
        response = self.client.put(self.detail_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.greek_to_greek.refresh_from_db()
        self.assertEqual(self.greek_to_greek.explanation, "Updated explanation")

    def test_delete_greek_to_greek_entry(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(GreekToGreek.objects.count(), 0)
