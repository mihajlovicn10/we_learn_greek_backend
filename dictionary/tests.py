from unittest import mock, skipUnless

from django.db import connection

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from dictionary.api.serializers import DictionarySerializer
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

    def test_create_entry_too_long(self):
        response = self.client.post(self.list_url, {
            "greek_word": "α" * 31,
            "pronounciation": "a",
            "translation": "too long",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("greek_word", response.data)

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

    def test_bulk_delete_rejects_malformed_ids(self):
        url = reverse("dictionary-bulk-delete")
        for payload in [{}, {"ids": []}, {"ids": "abc"}, {"ids": 5}, {"ids": ["x"]},
                        {"ids": [{"a": 1}]}, {"ids": [0]}, {"ids": [None]}]:
            response = self.client.post(url, payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, payload)
            self.assertIn("ids", response.data, payload)
        self.assertEqual(Dictionary.objects.count(), 1)

    def test_bulk_delete_only_deletes_own_entries(self):
        other = User.objects.create_user(email="other@example.com", password="testpass")
        foreign = Dictionary.objects.create(
            greek_word="φως", pronounciation="fos", translation="light", user=other,
        )
        response = self.client.post(
            reverse("dictionary-bulk-delete"),
            {"ids": [self.dictionary_entry.pk, foreign.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Dictionary.objects.filter(pk=foreign.pk).exists())
        self.assertFalse(Dictionary.objects.filter(pk=self.dictionary_entry.pk).exists())

    def test_greek_word_validation(self):
        accepted = {
            "ΟΥΡΑΝΌΣ": "ΟΥΡΑΝΌΣ",          # capitals with tonos
            "ο άνθρωπος": "ο άνθρωπος",     # article + noun
            "καλή   τύχη": "καλή τύχη",     # whitespace collapsed
            "ἄνθρωπος": "ἄνθρωπος",         # polytonic
            "Ϊσως": "Ϊσως",                 # capital with dialytika
        }
        for word, stored in accepted.items():
            response = self.client.post(self.list_url, {
                "greek_word": word, "pronounciation": "xx", "translation": "t",
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, word)
            self.assertEqual(response.data["greek_word"], stored, word)

        for word in ["logos", "λόγος1", "λόγος!", "λόγοs"]:
            response = self.client.post(self.list_url, {
                "greek_word": word, "pronounciation": "xx", "translation": "t",
            })
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, word)
            self.assertIn("greek_word", response.data, word)

    # SQLite's case-insensitive matching is ASCII-only, so this only holds on Postgres.
    @skipUnless(connection.vendor == "postgresql", "needs Unicode-aware iexact")
    def test_duplicate_check_ignores_greek_case(self):
        response = self.client.post(self.list_url, {
            "greek_word": "ΛΌΓΟΣ", "pronounciation": "logos", "translation": "word",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("greek_word", response.data)

    def test_concurrent_duplicate_returns_400(self):
        # Skip the serializer's duplicate check, as when two requests race past it.
        with mock.patch.object(DictionarySerializer, "validate_greek_word", lambda self, value: value):
            response = self.client.post(self.list_url, {
                "greek_word": "λόγος", "pronounciation": "logos", "translation": "word",
            })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["greek_word"][0], "You already have this word in your dictionary")
        self.assertEqual(Dictionary.objects.count(), 1)


class DictionarySearchTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="learner@example.com", password="testpass")
        other = User.objects.create_user(email="other@example.com", password="testpass")
        Dictionary.objects.create(user=self.user, greek_word="Καλημέρα", pronounciation="Kaliméra", translation="Good morning")
        Dictionary.objects.create(user=self.user, greek_word="Ευχαριστώ", pronounciation="Efcharistó", translation="Thank you")
        Dictionary.objects.create(user=other, greek_word="Καληνύχτα", pronounciation="Kaliníhta", translation="Good night")
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def search(self, term):
        response = self.client.get(reverse("dictionary-list"), {"search": term})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [w["greek_word"] for w in response.data["results"]]

    def test_search_is_accent_insensitive_and_accepts_latin(self):
        self.assertEqual(self.search("καλημερα"), ["Καλημέρα"])
        self.assertEqual(self.search("kalimera"), ["Καλημέρα"])
        self.assertEqual(self.search("thank"), ["Ευχαριστώ"])

    def test_search_stays_scoped_to_the_user(self):
        self.assertEqual(self.search("καλη"), ["Καλημέρα"])
