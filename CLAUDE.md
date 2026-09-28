# CLAUDE.md

Django REST API for **We Learn Greek**, a Greek-learning app. The React frontend is in a separate repo at
`../frontend/we_learn_greek_frontend`. Its API contract is `src/constants/endpoints.js`; check it before
renaming or removing any route.

## Commands

```bash
source .venv/bin/activate
pip install -r requirements.txt

# Tests: ALWAYS blank DATABASE_URL. .env points at the Neon (production) database,
# and without this the test runner creates its test DB on Neon.
DATABASE_URL= python manage.py test
DATABASE_URL= python manage.py test dictionary          # one app
DATABASE_URL= python manage.py makemigrations --check --dry-run

# Before pushing, also run against Postgres, which is what production and CI use. SQLite
# skips checks Postgres enforces (varchar length, Unicode case-insensitive matching).
# Docker: `docker compose up -d`, then DATABASE_URL=postgresql://postgres:postgres@localhost:5432/we_learn_greek
# No Docker: Homebrew postgresql@16 is installed. Use initdb + pg_ctl on a spare port
# (e.g. 55432) with -c unix_socket_directories='' if the data dir path is long.
DATABASE_URL=postgresql://... DEBUG=false SECRET_KEY=<50+ random chars> SECURE_SSL_REDIRECT=false python manage.py test

DATABASE_URL= python manage.py runserver                # local SQLite
docker compose up -d                                     # local Postgres; then
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/we_learn_greek python manage.py migrate
```

Swagger is at `/swagger/` and ReDoc at `/redoc/`.

CI (`.github/workflows/ci.yml`) runs on push to main, on PRs, and weekly. It sets DEBUG=false against a Postgres 16
service and runs `makemigrations --check`, `check --deploy --fail-level WARNING`, `collectstatic` and the tests.
A separate job runs `pip-audit -r requirements.txt`. If you change a security setting, make sure `check --deploy`
still passes. `SILENCED_SYSTEM_CHECKS` only covers the HSTS subdomain/preload checks.

Deploy target: Render web service (`render.yaml`, `build.sh` runs `collectstatic` + `migrate`) with a Neon Postgres DB.
Never run `migrate` against the Neon URL unless the user asks for it.

## Layout

| App | Purpose | Storage today | Target |
|-----|---------|---------------|--------|
| `we_learn_greek/` | Project settings, URLs, custom `User` (email login, JWT auth) | Postgres | Postgres |
| `dictionary/` | The user's personal word list ("learned words"). Auth required, scoped to `request.user` | Postgres | Postgres |
| `conjugator/` | Verbs: `Verb`, 36 flat conjugation columns (6 tenses × 6 persons) | Postgres | static JSON |
| `declinator/` | Nouns: `Noun`, 8 case/number columns + gender | Postgres | static JSON |
| `greek_to_greek/` | Monolingual definitions (`word`, `explanation`) | Postgres | static JSON |
| `transparrent/` | "Transparent" words (Greek → cognate in another language) | Postgres | static JSON |

Each app follows the same pattern: `models.py`, `api/serializers.py`, `views.py` (DRF viewset), and `urls.py`
(a `DefaultRouter` plus legacy alias routes such as `conjugator/` and `*-entries/`). All apps mount under `/api/`.

## Architecture decisions (already made, don't re-litigate)

- **Word data becomes static JSON**, organized by difficulty tier 1–5 (verbs, nouns, Greek-to-Greek, transparent
  words). It is read-only reference content shipped with the code, not user data.
- **Postgres is only for users and their dictionary entries.**
- The word-data endpoints are **read-only** (`ReadOnlyModelViewSet`). Never re-add write methods to them. Content
  changes go through the data files (Django admin during the transition).

## Conventions and gotchas

- Settings are production-safe by default. `DEBUG` is off unless set, and when it is off `SECRET_KEY` is required
  and HTTPS redirect, secure cookies and HSTS are enabled. `.env.example` lists the other environment variables.
- Default permission is `IsAuthenticated`. Public views must opt in with `permission_classes = [AllowAny]`.
- Auth: `USERNAME_FIELD = "email"`, and `User.username` has been removed (migration 0008). Emails are stored
  lowercased, and lookups and uniqueness are case-insensitive (migration 0009). Register runs Django's password
  validators. Log in with `POST /api/token/` or `/api/login/`. Both return a JWT pair.
- JWT: access tokens last 15 min and refresh tokens 1 day. Refresh tokens **rotate**: every refresh returns a new
  one and blacklists the old one (`token_blacklist` app). `POST /api/logout/ {refresh}` blacklists a token.
  Changing a password revokes all of that user's tokens (`CHECK_REVOKE_TOKEN`; our refresh serializer enforces it
  too). The frontend depends on this: `axiosConfig.js` shares a single refresh request between concurrent 401s and
  stores the rotated token.
- Rate limits (`DEFAULT_THROTTLE_RATES`, all overridable by env):
  - `auth`: login and register
  - `token`: refresh and logout
  - `admin_login`: `admin_site.ThrottledAdminSite`
  - `content_burst` / `content_sustained`: word viewsets, via `we_learn_greek.throttling.CONTENT_THROTTLES`

  New word/content endpoints must use `CONTENT_THROTTLES`. Counters live in the default cache: LocMem when
  DEBUG is on, and the Postgres `django_cache` table otherwise, so they're shared across gunicorn workers.
  `build.sh` runs `createcachetable` and `flushexpiredtokens`. Tests that make many throttled requests must
  call `cache.clear()` in `setUp`, and should lower a rate with
  `mock.patch.dict(SomeThrottle.THROTTLE_RATES, ...)`, because `override_settings` doesn't reach throttle
  classes.
- Admin: `ADMIN_ENABLED` / `ADMIN_URL` env vars. `django.contrib.admin` is replaced in `INSTALLED_APPS` by
  `we_learn_greek.admin_site.ThrottledAdminConfig`.
- Pagination: `we_learn_greek.pagination.StandardPagination` honours `?page_size=` (the frontend sends 5), capped at 50.
- Static files use WhiteNoise `CompressedManifestStaticFilesStorage` through `STORAGES`. Any test that renders
  `{% static %}` (Swagger or admin) must override `STORAGES` with plain `StaticFilesStorage`, as `ApiDocsTests` does.
- The misspellings are part of the public API and the DB schema. Don't "fix" them in passing, because the frontend
  depends on them: the app is named `transparrent`, the field is `Dictionary.pronounciation`, and the verb field is
  `Verb.present_third_pluran`.
- List responses are `{count, next, previous, results}`, including `transparent-words/by-language/<lang>/`,
  which also supports `?search=` and `?category=`.
- The `list_verbs`, `noun_detail`, etc. function views in each `views.py`, and all of `we_learn_greek/views.py`, are
  dead code. They are not routed and the templates don't exist.
- The `dictionary` model and serializer share `dictionary/validators.py:validate_greek` (Greek letters, including
  polytonic, with single spaces between words). The serializer redeclares `greek_word`, so it repeats
  `max_length` and collapses whitespace before validating. Duplicate words are a 400 keyed on `greek_word`,
  because the frontend displays `data.greek_word[0]`.
- Tests that depend on Postgres-only behavior use `@skipUnless(connection.vendor == "postgresql", ...)`.
- Viewsets whose `get_queryset` uses `request.user` must return `.none()` when `swagger_fake_view` is set, because
  drf-yasg builds the schema without a user.
- Python 3.14.5 everywhere (`.python-version`, `runtime.txt`, `render.yaml`). `requirements.txt` is an exact
  `pip freeze`; bump versions deliberately.
- Tests use DRF's `APITestCase` / `APIClient`. Put tests in each app's `tests.py`. Add a regression test with
  every bug fix.
