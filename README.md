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

3. Create the PostgreSQL database and run migrations:

```bash
createdb we_learn_greek
python manage.py migrate
python manage.py createsuperuser
```

4. Start the server:

```bash
python manage.py runserver
```

API docs: http://127.0.0.1:8000/swagger/

## Auth

- Register: `POST /api/register/` with `email`, `password`, `first_name`, `last_name`
- Login: `POST /api/token/` or `POST /api/login/` with `email` and `password`
- Use the returned JWT as `Authorization: Bearer <access_token>`

## Deploy backend (free demo)

### Recommended: Render + Neon

Best free combo for a demo that lasts longer than 30 days:

| Piece | Service | Cost | Notes |
|-------|---------|------|-------|
| Backend | Render Web Service | Free | Sleeps after 15 min idle; cold start ~30-60s |
| Database | Neon PostgreSQL | Free | Does not expire after 30 days |
| Frontend | Vercel or Netlify | Free | For React/Next/Vue apps |

**Backend on Render**

1. Push this repo to GitHub.
2. Create a free PostgreSQL database on Neon and copy the connection string.
3. On Render: New Web Service, connect the repo.
4. Set environment variables:
   - `DATABASE_URL` = Neon connection string
   - `SECRET_KEY` = random string
   - `DEBUG` = false
   - `ALLOWED_HOSTS` = .onrender.com
   - `CORS_ALLOWED_ORIGINS` = your frontend URL
5. Build command: `./build.sh`
6. Start command: `gunicorn we_learn_greek.wsgi --log-file -`

Or use the included `render.yaml` blueprint. Swap Render free Postgres for Neon if you need the demo up longer than 30 days.

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
