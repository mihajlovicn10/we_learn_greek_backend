# Neon + Render setup

Use this checklist while connecting Neon and deploying from GitHub.

## 1. Neon (database)

1. Open [Neon Console](https://console.neon.tech) → your project.
2. Go to **Connection details**.
3. Copy the **Pooled connection** string (recommended for Render).
4. Ensure the URL ends with `?sslmode=require` (Neon usually includes this).

**Local `.env`:**

```bash
cp .env.example .env
# Paste into .env:
DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require
```

**Apply schema locally:**

```bash
chmod +x scripts/setup_neon.sh
./scripts/setup_neon.sh
```

Or:

```bash
python manage.py migrate
python manage.py createsuperuser
```

## 2. GitHub

Push this repo to `https://github.com/mihajlovicn10/we_learn_greek_backend`

Neon GitHub integration (optional): connects branches for preview DBs. Your main `DATABASE_URL` for production still comes from the Neon **main** branch connection string.

## 3. Render (web service)

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint** (or Web Service).
2. Connect the GitHub repo `we_learn_greek_backend`.
3. Set environment variables:

| Variable | Value |
|----------|--------|
| `DATABASE_URL` | Neon **pooled** connection string |
| `SECRET_KEY` | Generate a long random string |
| `DEBUG` | `false` |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | Your frontend URL when ready |

4. Build command: `./build.sh`
5. Start command: `gunicorn we_learn_greek.wsgi --log-file -`

`build.sh` runs `migrate` on every deploy, so tables are created automatically.

## 4. Verify deployment

```bash
curl https://your-app.onrender.com/api/verbs/
curl https://your-app.onrender.com/swagger/
```

## Connection types (Neon)

| Type | Use for |
|------|---------|
| **Pooled** | Render app runtime (recommended) |
| **Direct** | One-off local migrations if pooled fails |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `SSL connection required` | Add `?sslmode=require` to `DATABASE_URL` |
| `connection refused` locally | Check Neon project is active (free tier suspends after inactivity) |
| Migrations fail on Render | Confirm `DATABASE_URL` is set in Render env vars |
| Cold start 30–60s | Normal on Render free tier |
