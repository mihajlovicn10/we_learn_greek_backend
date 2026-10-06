from unittest import mock

from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from we_learn_greek.throttling import ContentBurstThrottle

from .models import Verb

User = get_user_model()


class VerbAPITestCase(TestCase):
    def setUp(self):
        cache.clear()  # content endpoints are rate limited
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
            "future_continuous_first_singular": "θα λύω",
            "future_continuous_second_singular": "θα λύεις",
            "future_continuous_third_singular": "θα λύει",
            "future_continuous_first_plural": "θα λύουμε",
            "future_continuous_second_plural": "θα λύετε",
            "future_continuous_third_plural": "θα λύουν",
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

    def test_future_continuous_in_verb_and_conjugation_endpoints(self):
        persons = ["first_singular", "second_singular", "third_singular", "first_plural", "second_plural", "third_plural"]
        for url in [f"/api/verbs/{self.verb.id}/", self.conjugation_url]:
            data = self.client.get(url).data
            self.assertEqual(
                [data[f"future_continuous_{p}"] for p in persons],
                ["θα λύω", "θα λύεις", "θα λύει", "θα λύουμε", "θα λύετε", "θα λύουν"],
                url,
            )

    def test_future_continuous_is_optional(self):
        older = {k: v for k, v in self.verb_data.items() if not k.startswith("future_continuous_")}
        verb = Verb.objects.create(**{**older, "infinitive": "γράφω"})
        data = self.client.get(f"/api/verbs/{verb.id}/conjugation/").data
        self.assertIsNone(data["future_continuous_first_singular"])

    def _create_verbs(self, count):
        for i in range(count):
            Verb.objects.create(**{**self.verb_data, "infinitive": f"ρήμα{i}"})

    def test_page_size_is_honoured_and_capped(self):
        self._create_verbs(60)
        response = self.client.get("/api/verbs/", {"page_size": 5})
        self.assertEqual(len(response.data["results"]), 5)
        response = self.client.get("/api/verbs/", {"page_size": 1000})
        self.assertEqual(len(response.data["results"]), 50)

    def test_content_endpoints_are_throttled(self):
        self.client.force_authenticate(user=None)
        with mock.patch.dict(ContentBurstThrottle.THROTTLE_RATES, {"content_burst": "3/min"}):
            statuses = [self.client.get("/api/verbs/").status_code for _ in range(4)]
        self.assertEqual(statuses, [200, 200, 200, 429])

    def test_search_is_accent_insensitive_and_accepts_latin(self):
        Verb.objects.create(**{**self.verb_data, "infinitive": "γράφω"})
        for term in ["γραφω", "grafo", "ΓΡΆΦΩ"]:
            with self.subTest(term=term):
                response = self.client.get("/api/verbs/", {"search": term})
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual([v["infinitive"] for v in response.data["results"]], ["γράφω"])


class VerbContentLoaderTests(TestCase):
    """load_content against copies of the real verbs file in a temp directory."""

    def setUp(self):
        import json, tempfile
        from pathlib import Path
        from django.conf import settings
        self.real = json.loads((Path(settings.BASE_DIR) / "content/verbs/tier-1.json").read_text(encoding="utf-8"))
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "verbs").mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def copy(self):
        import json
        return json.loads(json.dumps(self.real))

    def write(self, data):
        import json
        (self.tmp / "verbs" / "tier-1.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def load(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("load_content", "--dir", str(self.tmp), *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_repo_verbs_file_is_valid(self):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("load_content", "--check", stdout=out)
        self.assertIn("verbs/tier-1.json: OK", out.getvalue())

    def test_load_maps_tenses_and_is_idempotent(self):
        self.write(self.real)
        self.assertIn(f"{len(self.real['items'])} created", self.load())
        self.assertIn("0 created, 0 updated", self.load())
        grafo = Verb.objects.get(infinitive="γράφω")
        self.assertEqual(
            [getattr(grafo, f"{t}_first_singular") for t in
             ("present", "imperfect", "aorist", "future_continuous", "future", "perfect", "plusperfect")],
            ["γράφω", "έγραφα", "έγραψα", "θα γράφω", "θα γράψω", "έχω γράψει", "είχα γράψει"],
        )
        self.assertEqual(grafo.present_third_pluran, "γράφουν")
        eimai = Verb.objects.get(infinitive="είμαι")
        self.assertIsNone(eimai.aorist_first_singular)
        self.assertIsNone(eimai.plusperfect_third_plural)
        self.assertTrue(eimai.irregular)
        self.assertEqual(eimai.translations, {"en": "to be"})

    def test_reload_updates_and_deletes(self):
        self.write(self.real)
        self.load()
        data = self.copy()
        data["items"][0]["translations"] = {"en": "to exist"}
        removed = data["items"].pop()
        self.write(data)
        self.assertIn("1 updated", self.load())
        self.assertEqual(Verb.objects.get(tier=1, content_id=data["items"][0]["id"]).translations, {"en": "to exist"})
        self.assertFalse(Verb.objects.filter(infinitive=removed["infinitive"]).exists())

    def test_invalid_files_load_nothing(self):
        from django.core.management.base import CommandError
        cases = {
            "unknown verb_type": lambda d: d["items"][0].update(verb_type="C"),
            "irregular not bool": lambda d: d["items"][0].update(irregular="yes"),
            "tense with 5 forms": lambda d: d["items"][2]["conjugation"]["present"].pop(),
            "missing tense": lambda d: d["items"][2]["conjugation"].pop("pluperfect"),
            "Latin letters": lambda d: d["items"][2]["conjugation"]["aorist"].__setitem__(0, "ekana"),
            "present is null": lambda d: d["items"][2]["conjugation"].update(present=None),
            "infinitive vs present": lambda d: d["items"][2].update(infinitive="κάνει"),
            "duplicate infinitive": lambda d: d["items"][3].update(infinitive=d["items"][2]["infinitive"]),
            "wrong schema": lambda d: d.update(schema="nouns/v1"),
        }
        for name, break_it in cases.items():
            with self.subTest(name):
                data = self.copy()
                break_it(data)
                self.write(data)
                with self.assertRaises(CommandError):
                    self.load()
                self.assertEqual(Verb.objects.count(), 0)


class VerbContentAPITests(TestCase):
    def setUp(self):
        from io import StringIO
        from django.core.management import call_command
        cache.clear()
        call_command("load_content", stdout=StringIO())  # the real content/ files
        self.client = APIClient()

    def test_filters(self):
        self.assertEqual(self.client.get("/api/verbs/", {"tier": 1}).data["count"], 99)
        self.assertEqual(self.client.get("/api/verbs/", {"irregular": "true"}).data["count"], 19)
        self.assertEqual(self.client.get("/api/verbs/", {"verb_type": "B1"}).data["count"], 22)

    def test_verb_fields(self):
        verb = self.client.get("/api/verbs/", {"search": "eimai"}).data["results"][0]
        self.assertEqual((verb["infinitive"], verb["irregular"], verb["translations"]), ("είμαι", True, {"en": "to be"}))
        self.assertIsNone(verb["aorist_first_singular"])
        self.assertNotIn("content_id", verb)
        conjugation = self.client.get(f"/api/verbs/{verb['id']}/conjugation/").data
        self.assertEqual(conjugation["future_continuous_first_singular"], "θα είμαι")
        self.assertEqual(conjugation["translations"], {"en": "to be"})
