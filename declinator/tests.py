from django.core.cache import cache
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


class NounSearchTests(TestCase):
    """?search= is accent-insensitive and accepts Latin letters."""

    def setUp(self):
        cache.clear()  # content endpoints are rate limited
        forms = {
            "άνθρωπος": ("άνθρωπος", "ανθρώπου", "άνθρωπο", "άνθρωπε", "άνθρωποι", "ανθρώπων", "ανθρώπους", "άνθρωποι"),
            "σπίτι": ("σπίτι", "σπιτιού", "σπίτι", "σπίτι", "σπίτια", "σπιτιών", "σπίτια", "σπίτια"),
        }
        fields = [
            "nominative_singular", "genitive_singular", "accusative_singular", "vocative_singular",
            "nominative_plural", "genitive_plural", "accusative_plural", "vocative_plural",
        ]
        for noun, values in forms.items():
            Noun.objects.create(basic_noun=noun, gender="masculine", **dict(zip(fields, values)))

    def search(self, term):
        response = self.client.get("/api/nouns/", {"search": term})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [noun["basic_noun"] for noun in response.data["results"]]

    def test_search_without_accents(self):
        self.assertEqual(self.search("ανθρωπος"), ["άνθρωπος"])

    def test_search_in_latin_letters(self):
        self.assertEqual(self.search("anthropos"), ["άνθρωπος"])
        self.assertEqual(self.search("spiti"), ["σπίτι"])

    def test_search_matches_other_forms_and_prefixes(self):
        self.assertEqual(self.search("σπιτια"), ["σπίτι"])
        self.assertEqual(self.search("ΑΝΘΡ"), ["άνθρωπος"])

    def test_search_without_match_is_empty(self):
        self.assertEqual(self.search("θάλασσα"), [])
