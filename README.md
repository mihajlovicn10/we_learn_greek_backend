# We Learn Greek — Backend API

Django REST API for a Greek language learning demo: verb conjugations, noun declensions, personal dictionary, Greek-to-Greek definitions, and cognate words.

## Local setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy environment variables and adjust as needed:

```bash
cp .env.example .env
```

## Database (Neon)

This project uses **PostgreSQL via Neon**. See **[docs/NEON_SETUP.md](docs/NEON_SETUP.md)** for the full checklist.

**Quick local setup:**

```bash
cp .env.example .env
# Paste your Neon pooled connection string into DATABASE_URL
chmod +x scripts/setup_neon.sh
./scripts/setup_neon.sh
```

Without `DATABASE_URL`, Django falls back to SQLite for quick local runs only — **not** for production.

4. Start the server:

```bash
python manage.py runserver
```

API docs: http://127.0.0.1:8000/swagger/

## Auth

- Register: `POST /api/register/` with `email`, `password`, `first_name`, `last_name`
- Login: `POST /api/token/` or `POST /api/login/` with `email` and `password`
- Use the returned JWT as `Authorization: Bearer <access_token>`

## Database options

| Where | Option | Notes |
|-------|--------|-------|
| **Local** | `docker compose up -d` | Easiest; no Postgres install needed |
| **Local** | SQLite | Automatic fallback if `DATABASE_URL` is unset |
| **Production** | [Neon](https://neon.tech) | Free, does not expire (recommended) |
| **Production** | [Render Postgres](https://render.com/docs/free#free-postgres) | Free, but **expires after 30 days** |

**Does Render support PostgreSQL?** Yes. Render offers managed Postgres and can auto-wire `DATABASE_URL` via `render.yaml`. For a long-lived demo, use Neon for the database and Render only for the web service.

## Deploy backend (free demo)

### Recommended: Render + Neon

| Piece | Service | Notes |
|-------|---------|-------|
| Backend | Render Web Service | Free; cold start ~30–60s |
| Database | **Neon** (you already have this) | Paste pooled `DATABASE_URL` into Render |
| Frontend | Vercel or Netlify | When ready |

Full steps: **[docs/NEON_SETUP.md](docs/NEON_SETUP.md)**

**Render env vars** (minimum):

```
DATABASE_URL=<neon pooled connection string>
SECRET_KEY=<random string>
DEBUG=false
ALLOWED_HOSTS=.onrender.com
```

**Frontend on Vercel / Netlify**

1. Deploy your frontend repo.
2. Set your API base URL env var to the Render backend URL.
3. Add the frontend URL to backend `CORS_ALLOWED_ORIGINS`.

### Alternative free options

| Platform | Good for | Caveat |
|----------|----------|--------|
| Render (all-in-one) | Backend + DB + static site | Free Postgres expires after 30 days |
| Railway | Backend + Postgres | Limited monthly credit |
| PythonAnywhere | Django only | Limited outbound HTTP on free tier |
| Cloudflare Pages | Frontend | Free CDN |
| GitHub Pages | Static frontend | No server-side rendering |

## API endpoints

| Resource | Path |
|----------|------|
| Verbs | `/api/verbs/` |
| Nouns | `/api/nouns/` |
| Dictionary (auth required) | `/api/dictionary/` |
| Greek-to-Greek | `/api/greek-to-greek/` |
| Transparent words | `/api/transparent-words/` |
