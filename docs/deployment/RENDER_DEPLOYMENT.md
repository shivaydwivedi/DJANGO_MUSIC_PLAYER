# Render Deployment

This guide describes the initial Render deployment path for Sonica Music
Player.

## Architecture

- Render Python Web Service.
- Render managed PostgreSQL database.
- WhiteNoise for static files.
- Waitress as the WSGI server.
- GitHub-connected deploys from `deployment/production-launch`.
- `/health/` as the Render health-check path.
- `/ready/` for database readiness verification after deploy.
- No persistent disk for the first deployment.
- No commercial or local media files deployed.

## Prerequisites

- A Render account.
- The GitHub repository connected to Render.
- The `deployment/production-launch` branch pushed to GitHub.
- No `.env`, local database, uploaded media, or collected static output in Git.

## Blueprint Flow

The repository includes `render.yaml`. In Render:

1. Open Blueprints.
2. Create a new Blueprint instance.
3. Select the GitHub repository.
4. Apply the Blueprint.
5. Let Render create the web service and PostgreSQL database.

The Blueprint defines one Python web service named `sonica-music-player` and one
PostgreSQL database named `sonica-postgres`.

## Environment Variables

The Blueprint sets:

| Variable | Source |
| --- | --- |
| `DEBUG` | `False` |
| `SECRET_KEY` | Render-generated secret |
| `DATABASE_URL` | Render Postgres internal connection string |
| `DATABASE_CONN_MAX_AGE` | `60` |
| `DATABASE_SSL_REQUIRE` | `False` for Render private-network database traffic |
| `ALLOWED_HOSTS` | `sonica-music-player.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://sonica-music-player.onrender.com` |
| `SECURE_SSL_REDIRECT` | `True` |
| `SESSION_COOKIE_SECURE` | `True` |
| `CSRF_COOKIE_SECURE` | `True` |
| `SECURE_HSTS_SECONDS` | `0` until HTTPS is verified |
| `TRUST_X_FORWARDED_PROTO` | `True` |
| `ENABLE_GOOGLE_AUTH` | `False` |
| `SONICA_MAX_AUDIO_UPLOAD_SIZE` | `20971520` |
| `SONICA_MAX_COVER_UPLOAD_SIZE` | `5242880` |

Render also supplies `RENDER_EXTERNAL_HOSTNAME`. Sonica adds that exact hostname
to `ALLOWED_HOSTS` and its HTTPS origin to `CSRF_TRUSTED_ORIGINS`. Custom
domains can be added later by updating the explicit environment variables.

## Build Command

```bash
bash scripts/render-build.sh
```

The script:

1. installs `requirements.txt`;
2. runs `collectstatic --noinput`;
3. runs `migrate --noinput`.

Render's pre-deploy command is the cleaner migration location for paid web
services. The initial free-friendly configuration runs migrations in the build
script because pre-deploy commands are not available on free web services. The
migration command is idempotent and runs once per deploy build, not once per web
request.

## Start Command

```bash
bash scripts/render-start.sh
```

The start script runs:

```bash
waitress-serve --listen="0.0.0.0:${PORT:-10000}" musicplayer.wsgi:application
```

Render provides `PORT`; the fallback is only for local start-script testing.

## Health And Readiness

Render health check path:

```text
/health/
```

After the service is live, verify database readiness:

```text
/ready/
```

`/ready/` returns `503` if the database is unavailable and does not expose
database credentials or exception details.

## Superuser Creation

Do not commit superuser credentials. After the first successful deployment,
create an admin user from a Render shell:

```bash
python manage.py createsuperuser
```

Use credentials stored outside the repository.

## Demo Data

The optional demo-data command creates fictional metadata only:

```bash
python manage.py seed_demo_catalog
```

Run it once manually from a Render shell only after deployment and migrations
have succeeded. Do not add it to every build command or application startup. It
does not download files, attach media paths, create users, or add copyrighted
songs.

## Media Limitation

The first deployment intentionally has no persistent media storage. Uploaded
files written to Render's ephemeral app filesystem are not durable. Use blank
media fields and Sonica's missing-cover and missing-audio fallbacks.

Media remains unavailable until legal persistent media storage is configured. Do
not deploy local commercial audio, cover art, files from `media/`, or
`db.sqlite3`.

## First Deploy Checklist

- Confirm `render.yaml` is committed to the deployment branch.
- Confirm `.python-version` is `3.12.13`.
- Confirm `.env`, `db.sqlite3`, `media/*`, and `staticfiles/` are not in Git.
- Apply the Blueprint in Render.
- Confirm the build installs dependencies, collects static files, and applies
  migrations.
- Confirm the service starts with Waitress.
- Visit `/health/`.
- Visit `/ready/`.
- Create a superuser from a Render shell if admin access is needed.
- Optionally run `seed_demo_catalog` once from a Render shell.
- Log in and verify browsing, favourites, playlists, and recent history with
  authorized demo content only.

## Rollback

If a deploy fails, Render keeps the previous successful deploy running. If a
bad deploy becomes live:

1. Roll back to the previous successful deploy in Render.
2. Review migration reversibility before rolling the database back.
3. Restore a database backup only if the release plan requires data rollback.
4. Re-run `/health/`, `/ready/`, `check --deploy`, and
   `deployment_readiness_check`.

## Free-Tier Limitations

- Pre-deploy commands are not available on free web services.
- No persistent disk is configured.
- Free services and databases are suitable for a first deployment rehearsal, not
  durable portfolio hosting.
- Media uploads are not persistent.

## Upgrade Path

For a long-lived portfolio deployment:

- move migrations to Render's pre-deploy command on a paid web service;
- upgrade the PostgreSQL plan;
- add backups and monitoring;
- configure a custom domain;
- verify HTTPS, then consider a staged positive `SECURE_HSTS_SECONDS`;
- add durable media storage through a persistent disk or object storage.
