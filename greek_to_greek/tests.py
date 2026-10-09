from django.core.cache import cache
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

    def test_search_filters_results(self):
        # Regression: this viewset had no search backend, so ?search= returned every word.
        cache.clear()  # content endpoints are rate limited
        GreekToGreek.objects.create(word="θάλασσα", explanation="Μεγάλη έκταση αλμυρού νερού.")
        for term, expected in [("θαλασσα", ["θάλασσα"]), ("thalasa", ["θάλασσα"]), ("νερου", ["θάλασσα"])]:
            with self.subTest(term=term):
                response = self.client.get(self.list_url, {"search": term})
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual([w["word"] for w in response.data["results"]], expected)


class GreekToGreekContentLoaderTests(APITestCase):
    """load_content against copies of the real Greek-to-Greek file in a temp directory."""

    def setUp(self):
        import json, tempfile
        from pathlib import Path
        from django.conf import settings
        self.real = json.loads(
            (Path(settings.BASE_DIR) / "content/greek-to-greek/tier-1.json").read_text(encoding="utf-8"))
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "greek-to-greek").mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def copy(self):
        import json
        return json.loads(json.dumps(self.real))

    def write(self, data):
        import json
        (self.tmp / "greek-to-greek" / "tier-1.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def load(self):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("load_content", "--dir", str(self.tmp), stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_repo_file_is_valid(self):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("load_content", "--check", stdout=out)
        self.assertIn("greek-to-greek/tier-1.json: OK", out.getvalue())

    def test_load_is_idempotent_and_syncs(self):
        self.write(self.real)
        self.assertIn(f"{len(self.real['items'])} created", self.load())
        self.assertIn("0 created, 0 updated", self.load())
        entry = GreekToGreek.objects.get(word="άνθρωπος")
        self.assertEqual((entry.pos, entry.translations), ("noun", {"en": "person, human"}))
        data = self.copy()
        data["items"][0]["explanation"] = "Νέα εξήγηση."
        removed = data["items"].pop()
        self.write(data)
        self.assertIn("1 updated", self.load())
        self.assertEqual(GreekToGreek.objects.get(word="άνθρωπος").explanation, "Νέα εξήγηση.")
        self.assertFalse(GreekToGreek.objects.filter(word=removed["word"]).exists())

    def test_invalid_files_load_nothing(self):
        from django.core.management.base import CommandError
        cases = {
            "unknown pos": lambda d: d["items"][0].update(pos="thing"),
            "Latin word": lambda d: d["items"][0].update(word="anthropos"),
            "empty explanation": lambda d: d["items"][0].update(explanation="  "),
            "explanation not in Greek": lambda d: d["items"][0].update(explanation="A living being."),
            "explanation too long": lambda d: d["items"][0].update(explanation="λέξη " * 120),
            "duplicate word": lambda d: d["items"][1].update(word=d["items"][0]["word"]),
            "missing translations": lambda d: d["items"][0].pop("translations"),
            "wrong schema": lambda d: d.update(schema="nouns/v1"),
        }
        for name, break_it in cases.items():
            with self.subTest(name):
                data = self.copy()
                break_it(data)
                self.write(data)
                with self.assertRaises(CommandError):
                    self.load()
                self.assertEqual(GreekToGreek.objects.count(), 0)


class GreekToGreekContentAPITests(APITestCase):
    def setUp(self):
        from io import StringIO
        from django.core.cache import cache
        from django.core.management import call_command
        cache.clear()
        call_command("load_content", stdout=StringIO())  # the real content/ files

    def test_filters_and_fields(self):
        self.assertEqual(self.client.get("/api/greek-to-greek/", {"tier": 1}).data["count"], 278)
        self.assertEqual(self.client.get("/api/greek-to-greek/", {"pos": "verb", "tier": 1}).data["count"], 99)
        entry = self.client.get("/api/greek-to-greek/", {"search": "anthropos"}).data["results"][0]
        self.assertEqual(entry["word"], "άνθρωπος")
        self.assertEqual(entry["translations"], {"en": "person, human"})
        self.assertNotIn("content_id", entry)
