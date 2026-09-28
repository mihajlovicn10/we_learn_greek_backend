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

    def test_write_methods_not_allowed(self):
        data = {"word": "φως", "explanation": "Light"}
        for url in [self.list_url, "/api/greek-to-greek-entries/"]:
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, url)
        detail_urls = [self.detail_url, f"/api/greek-to-greek-entries/{self.greek_to_greek.pk}/"]
        for url in detail_urls:
            for method in (self.client.put, self.client.patch, self.client.delete):
                response = method(url, data)
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, url)
        self.greek_to_greek.refresh_from_db()
        self.assertEqual(self.greek_to_greek.explanation, "Speech or reason")
        self.assertEqual(GreekToGreek.objects.count(), 1)

    def test_list_greek_to_greek_entries(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_greek_to_greek_entry(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["word"], "λόγος")
