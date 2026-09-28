from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Verb

User = get_user_model()


class VerbAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.verb_data = {
            "infinitive": "λύω",
            "verb_type": "A1",
            "present_first_singular": "λύω",
            "present_second_singular": "λύεις",
            "present_third_singular": "λύει",
            "present_first_plural": "λύομεν",
            "present_second_plural": "λύετε",
            "present_third_pluran": "λύουσι",
            "aorist_first_singular": "ἔλυσα",
            "aorist_second_singular": "ἔλυσας",
            "aorist_third_singular": "ἔλυσε",
            "aorist_first_plural": "ἐλύσαμεν",
            "aorist_second_plural": "ἐλύσατε",
            "aorist_third_plural": "ἔλυσαν",
            "imperfect_first_singular": "ἔλυον",
            "imperfect_second_singular": "ἔλυες",
            "imperfect_third_singular": "ἔλυε",
            "imperfect_first_plural": "ἐλύομεν",
            "imperfect_second_plural": "ἐλύετε",
            "imperfect_third_plural": "ἔλυον",
            "perfect_first_singular": "λέλυκα",
            "perfect_second_singular": "λέλυκας",
            "perfect_third_singular": "λέλυκε",
            "perfect_first_plural": "λελύκαμεν",
            "perfect_second_plural": "λελύκατε",
            "perfect_third_plural": "λέλυκαν",
            "plusperfect_first_singular": "ἐλελύκειν",
            "plusperfect_second_singular": "ἐλελύκεις",
            "plusperfect_third_singular": "ἐλελύκει",
            "plusperfect_first_plural": "ἐλελύκειμεν",
            "plusperfect_second_plural": "ἐλελύκειτε",
            "plusperfect_third_plural": "ἐλελύκεισαν",
            "future_first_singular": "λύσω",
            "future_second_singular": "λύσεις",
            "future_third_singular": "λύσει",
            "future_first_plural": "λύσομεν",
            "future_second_plural": "λύσετε",
            "future_third_plural": "λύσουσι",
        }

        self.verb = Verb.objects.create(**self.verb_data)
        self.api_url = "/api/conjugator/"
        self.conjugation_url = f"/api/verbs/{self.verb.id}/conjugation/"

    def test_write_methods_not_allowed(self):
        detail_urls = [f"{self.api_url}{self.verb.id}/", f"/api/verbs/{self.verb.id}/"]
        for url in [self.api_url, "/api/verbs/"]:
            response = self.client.post(url, self.verb_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, url)
        for url in detail_urls:
            for method in (self.client.put, self.client.patch, self.client.delete):
                response = method(url, self.verb_data, format="json")
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, url)
        self.verb.refresh_from_db()
        self.assertEqual(self.verb.infinitive, "λύω")
        self.assertEqual(Verb.objects.count(), 1)

    def test_retrieve_verb(self):
        response = self.client.get(f"{self.api_url}{self.verb.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["infinitive"], self.verb_data["infinitive"])

    def test_verb_conjugation_endpoint(self):
        response = self.client.get(self.conjugation_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["infinitive"], self.verb_data["infinitive"])
        self.assertIn("present_first_singular", response.data)
