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

    def test_create_verb(self):
        new_verb_data = self.verb_data.copy()
        new_verb_data["infinitive"] = "γράφω"
        response = self.client.post(self.api_url, new_verb_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Verb.objects.count(), 2)
        self.assertEqual(Verb.objects.last().infinitive, "γράφω")

    def test_retrieve_verb(self):
        response = self.client.get(f"{self.api_url}{self.verb.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["infinitive"], self.verb_data["infinitive"])

    def test_update_verb(self):
        updated_data = self.verb_data.copy()
        updated_data["infinitive"] = "παιδεύω"
        response = self.client.put(f"{self.api_url}{self.verb.id}/", updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.verb.refresh_from_db()
        self.assertEqual(self.verb.infinitive, "παιδεύω")

    def test_delete_verb(self):
        response = self.client.delete(f"{self.api_url}{self.verb.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Verb.objects.count(), 0)

    def test_create_verb_invalid_data(self):
        invalid_data = self.verb_data.copy()
        invalid_data.pop("infinitive")
        response = self.client.post(self.api_url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("infinitive", response.data)

    def test_verb_conjugation_endpoint(self):
        response = self.client.get(self.conjugation_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["infinitive"], self.verb_data["infinitive"])
        self.assertIn("present_first_singular", response.data)
