import json

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


class NounContentLoaderTests(TestCase):
    """load_content against copies of the real content file in a temp directory."""

    def setUp(self):
        import json, tempfile
        from pathlib import Path
        from django.conf import settings
        self.real = json.loads((Path(settings.BASE_DIR) / "content/nouns/tier-1.json").read_text(encoding="utf-8"))
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "nouns").mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def write(self, data, name="tier-1.json"):
        import json
        (self.tmp / "nouns" / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def load(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out, err = StringIO(), StringIO()
        call_command("load_content", "--dir", str(self.tmp), *args, stdout=out, stderr=err)
        return out.getvalue() + err.getvalue()

    def test_repo_content_files_are_valid(self):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("load_content", "--check", stdout=out)  # the real content/ directory, as CI runs it
        self.assertIn("nouns/tier-1.json: OK", out.getvalue())
        self.assertEqual(Noun.objects.count(), 0)  # --check never writes

    def test_load_is_idempotent(self):
        self.write(self.real)
        self.assertIn(f"{len(self.real['items'])} created", self.load())
        self.assertIn(f"0 created, 0 updated, {len(self.real['items'])} unchanged, 0 deleted", self.load())
        milk = Noun.objects.get(basic_noun="γάλα")
        self.assertIsNone(milk.nominative_plural)
        self.assertEqual(milk.translations, {"en": "milk"})

    def test_reload_updates_changed_and_deletes_removed_items(self):
        self.write(self.real)
        self.load()
        pk_before = Noun.objects.get(tier=1, content_id=1).pk
        data = json.loads(json.dumps(self.real))
        data["items"][0]["translations"] = {"en": "human being"}
        removed = data["items"].pop()
        self.write(data)
        self.assertIn("1 updated", self.load())
        noun = Noun.objects.get(tier=1, content_id=1)
        self.assertEqual((noun.pk, noun.translations), (pk_before, {"en": "human being"}))  # same row, so API ids are stable
        self.assertFalse(Noun.objects.filter(tier=1, content_id=removed["id"]).exists())

    def test_invalid_files_load_nothing(self):
        from django.core.management.base import CommandError
        cases = {
            "bad gender": lambda d: d["items"][0].update(gender="male"),
            "non-Greek form": lambda d: d["items"][0]["plural"].update(genitive="anthropon"),
            "missing case": lambda d: d["items"][0]["singular"].pop("vocative"),
            "duplicate id": lambda d: d["items"][1].update(id=d["items"][0]["id"]),
            "item tier mismatch": lambda d: d["items"][0].update(tier=2),
            "file tier mismatch": lambda d: d.update(tier=2),
            "basic_noun vs nominative": lambda d: d["items"][0].update(basic_noun="άντρας"),
            "wrong schema": lambda d: d.update(schema="verbs/v1"),
        }
        for name, break_it in cases.items():
            with self.subTest(name):
                data = json.loads(json.dumps(self.real))
                break_it(data)
                self.write(data)
                with self.assertRaises(CommandError):
                    self.load()
                self.assertEqual(Noun.objects.count(), 0)

    def test_bad_file_name_and_unknown_types(self):
        from django.core.management.base import CommandError
        (self.tmp / "verbs").mkdir()
        (self.tmp / "verbs" / "tier-1.json").write_text("{}", encoding="utf-8")
        self.write(self.real)
        self.assertIn("Skipping verbs/", self.load("--check"))
        self.write(self.real, name="tier1.json")
        with self.assertRaises(CommandError):
            self.load("--check")


class NounContentAPITests(TestCase):
    def setUp(self):
        cache.clear()
        common = {"gender": "neuter", "genitive_singular": "νερού", "accusative_singular": "νερό",
                  "vocative_singular": "νερό"}
        Noun.objects.create(tier=1, content_id=1, basic_noun="νερό", nominative_singular="νερό",
                            translations={"en": "water"}, **common)
        Noun.objects.create(tier=2, content_id=1, basic_noun="γάλα", nominative_singular="γάλα",
                            translations={"en": "milk"}, **common)
        self.client = APIClient()

    def test_list_exposes_tier_translations_and_null_forms(self):
        result = self.client.get("/api/nouns/", {"tier": 1}).data["results"]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tier"], 1)
        self.assertEqual(result[0]["translations"], {"en": "water"})
        self.assertIsNone(result[0]["nominative_plural"])

    def test_tier_filter(self):
        self.assertEqual(self.client.get("/api/nouns/").data["count"], 2)
        self.assertEqual(self.client.get("/api/nouns/", {"tier": 2}).data["count"], 1)
        self.assertEqual(self.client.get("/api/nouns/", {"tier": 5}).data["count"], 0)
        self.assertEqual(self.client.get("/api/nouns/", {"tier": "one"}).status_code, status.HTTP_400_BAD_REQUEST)
