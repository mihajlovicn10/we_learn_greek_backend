from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import TransparentWord


class TransparentWordAPITestCase(APITestCase):
    def setUp(self):
        cache.clear()  # content endpoints are rate limited
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

    def test_write_methods_not_allowed(self):
        data = {"language": "fr", "greek_word": "φιλοσοφία", "category": "Philosophy"}
        for url in [self.list_url, "/api/transparent-words-entries/"]:
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, url)
        detail_urls = [self.detail_url, f"/api/transparent-words-entries/{self.transparent_word.pk}/"]
        for url in detail_urls:
            for method in (self.client.put, self.client.patch, self.client.delete):
                response = method(url, data)
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED, url)
        self.transparent_word.refresh_from_db()
        self.assertEqual(self.transparent_word.category, "Science")
        self.assertEqual(TransparentWord.objects.count(), 1)

    def test_list_transparent_words(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_transparent_word(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["greek_word"], "πρόβλημα")

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
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_by_language_search_category_and_pagination(self):
        for greek, word, category in [
            ("θέατρο", "theatre", "Arts"),
            ("μουσική", "music", "Arts"),
            ("φυσική", "physics", "Science"),
        ]:
            TransparentWord.objects.create(
                language="en", greek_word=greek, language_word=word, category=category,
            )
        url = "/api/transparent-words/by-language/en/"

        response = self.client.get(url, {"category": "arts"})
        self.assertEqual(response.data["count"], 2)

        response = self.client.get(url, {"search": "music"})
        self.assertEqual([w["greek_word"] for w in response.data["results"]], ["μουσική"])

        response = self.client.get(url, {"page_size": 2, "page": 2})
        self.assertEqual(response.data["count"], 4)
        self.assertEqual(len(response.data["results"]), 2)

    def test_search_is_accent_insensitive_and_accepts_latin(self):
        for term in ["προβλημα", "provlima", "PROBLEM"]:
            with self.subTest(term=term):
                response = self.client.get(self.language_url, {"search": term})
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual([w["greek_word"] for w in response.data["results"]], ["πρόβλημα"])


class TransparentContentLoaderTests(APITestCase):
    """load_content against copies of the real per-language files in a temp directory."""

    def setUp(self):
        import json, tempfile
        from pathlib import Path
        from django.conf import settings
        src = Path(settings.BASE_DIR) / "content/transparent-words"
        self.real = {lang: json.loads((src / f"{lang}.json").read_text(encoding="utf-8")) for lang in ("en", "fr", "de")}
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "transparent-words").mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def copy(self, lang):
        import json
        return json.loads(json.dumps(self.real[lang]))

    def write(self, data, name):
        import json
        (self.tmp / "transparent-words" / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def load(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("load_content", "--dir", str(self.tmp), *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_repo_files_are_valid(self):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("load_content", "--check", stdout=out)
        for lang in ("en", "fr", "de", "es", "it", "ru"):
            self.assertIn(f"transparent-words/{lang}.json: OK", out.getvalue())

    def test_each_file_owns_its_language(self):
        for lang in ("en", "fr", "de"):
            self.write(self.real[lang], f"{lang}.json")
        self.load()
        self.assertEqual(TransparentWord.objects.filter(language="de").count(), len(self.real["de"]["items"]))
        self.assertIn("0 created, 0 updated", self.load())
        # Editing and trimming the French file touches only French rows.
        data = self.copy("fr")
        data["items"][0]["language_word"] = "téléphone fixe"
        removed = data["items"].pop()
        self.write(data, "fr.json")
        output = self.load()
        self.assertIn("transparent-words/fr.json: 0 created, 1 updated", output)
        self.assertIn("transparent-words/en.json: 0 created, 0 updated", output)
        self.assertFalse(TransparentWord.objects.filter(language="fr", greek_word=removed["greek_word"]).exists())
        self.assertTrue(TransparentWord.objects.filter(language="en", greek_word=removed["greek_word"]).exists())

    def test_invalid_files_load_nothing(self):
        from django.core.management.base import CommandError
        cases = {
            "unknown category": lambda d: d["items"][0].update(category="Sport"),
            "item language mismatch": lambda d: d["items"][0].update(language="fr"),
            "file language mismatch": lambda d: d.update(language="fr"),
            "Latin greek_word": lambda d: d["items"][0].update(greek_word="tilefono"),
            "example not in Greek": lambda d: d["items"][0].update(example_greek="The phone rings."),
            "empty language_word": lambda d: d["items"][0].update(language_word=""),
            "tier out of range": lambda d: d["items"][0].update(tier=9),
            "duplicate greek_word": lambda d: d["items"][1].update(greek_word=d["items"][0]["greek_word"]),
            "missing etymology": lambda d: d["items"][0].pop("etymology"),
        }
        for name, break_it in cases.items():
            with self.subTest(name):
                data = self.copy("en")
                break_it(data)
                self.write(data, "en.json")
                with self.assertRaises(CommandError):
                    self.load()
                self.assertEqual(TransparentWord.objects.count(), 0)

    def test_file_names(self):
        from django.core.management.base import CommandError
        for name in ("tier-1.json", "english.json", "xx.json"):  # xx: not a supported language
            with self.subTest(name):
                for old in (self.tmp / "transparent-words").glob("*.json"):
                    old.unlink()
                self.write(self.copy("en"), name)
                with self.assertRaises(CommandError):
                    self.load("--check")


class TransparentContentAPITests(APITestCase):
    def setUp(self):
        from io import StringIO
        from django.core.management import call_command
        cache.clear()
        call_command("load_content", stdout=StringIO())  # the real content/ files

    def test_by_language_counts_and_filters(self):
        def count(url, **params):
            cache.clear()
            return self.client.get(url, params).data["count"]
        self.assertEqual(count("/api/transparent-words/by-language/en/"), 71)
        self.assertEqual(count("/api/transparent-words/by-language/fr/"), 71)
        self.assertEqual(count("/api/transparent-words/by-language/de/"), 70)
        self.assertEqual(count("/api/transparent-words/by-language/es/"), 69)
        self.assertEqual(count("/api/transparent-words/by-language/it/"), 68)
        self.assertEqual(count("/api/transparent-words/by-language/ru/"), 67)
        self.assertEqual(count("/api/transparent-words/by-language/en/", category="arts"), 12)
        self.assertEqual(count("/api/transparent-words/", language="de", tier=1), 70)
        cache.clear()
        self.assertEqual(self.client.get("/api/transparent-words/", {"tier": "x"}).status_code, status.HTTP_400_BAD_REQUEST)

    def test_entry_fields(self):
        entry = self.client.get("/api/transparent-words/by-language/fr/", {"search": "telephone"}).data["results"][0]
        self.assertEqual((entry["greek_word"], entry["language_word"], entry["tier"]), ("τηλέφωνο", "téléphone", 1))
        self.assertNotIn("content_id", entry)
