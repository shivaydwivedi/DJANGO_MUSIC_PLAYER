# PostgreSQL Deployment

## Phase 16 Scope

Branch: `modernization/postgresql-deployment`

This phase prepares Sonica for a real PostgreSQL-backed production deployment
without performing a public deployment and without transferring local SQLite
data.

## Architecture Decision

Sonica keeps SQLite as the local default and selects PostgreSQL only when
`DATABASE_URL` is supplied. Database URLs are parsed with `dj-database-url`, and
PostgreSQL uses `psycopg` 3 for Python 3.12 and Django 5.2 compatibility.

Static files are served in production with WhiteNoise using compressed manifest
storage. Waitress remains the production WSGI server because the app is a
synchronous Django WSGI application and Waitress is already part of the verified
runtime.

## Local SQLite Behavior

When `DATABASE_URL` is empty or unset:

- Django uses `django.db.backends.sqlite3`.
- The database file remains `db.sqlite3` in the project root.
- Existing local development, tests, and project smoke checks continue to work
  without PostgreSQL.

SQLite is not recommended for real multi-user production. It is retained for
safe local development and demos.

## Production PostgreSQL Configuration

Set `DATABASE_URL` in the deployment environment, never in source control.

Example format only:

```text
postgresql://sonica_user:replace-with-password@db.example.com:5432/sonica
```

Supported database environment variables:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Selects the production database and credentials. |
| `DATABASE_CONN_MAX_AGE` | Persistent connection lifetime in seconds. Defaults to `60` when `DATABASE_URL` is set. |
| `DATABASE_SSL_REQUIRE` | Adds provider-compatible SSL mode when set to `True`. |

Many managed PostgreSQL providers require SSL. Enable `DATABASE_SSL_REQUIRE=True`
when the provider requires encrypted connections. Leave it `False` for local or
private disposable PostgreSQL instances that do not support SSL.

## Required Environment Variables

Production deployments must review:

- `DJANGO_SETTINGS_MODULE`, only when the platform does not use the default
  `musicplayer.settings`;
- `SECRET_KEY`;
- `DEBUG`;
- `ALLOWED_HOSTS`;
- `CSRF_TRUSTED_ORIGINS`;
- `DATABASE_URL`;
- `DATABASE_CONN_MAX_AGE`;
- `DATABASE_SSL_REQUIRE`;
- `PORT`;
- `SECURE_SSL_REDIRECT`;
- `SESSION_COOKIE_SECURE`;
- `CSRF_COOKIE_SECURE`;
- `SECURE_HSTS_SECONDS`;
- `TRUST_X_FORWARDED_PROTO`;
- `ENABLE_GOOGLE_AUTH`;
- `SONICA_MAX_AUDIO_UPLOAD_SIZE`;
- `SONICA_MAX_COVER_UPLOAD_SIZE`.

Do not store real passwords, OAuth credentials, database URLs, or production
domains in the repository.

## Migration Commands

Run migrations against the target production database after taking a database
backup:

```powershell
.\.venv-django52\Scripts\python.exe manage.py migrate --noinput
```

`migrate` creates or updates schema. It does not transfer rows from local
SQLite to PostgreSQL. If existing production data must move, use a planned
backup/export/import process on copied data first.

This phase did not execute migrations against a real PostgreSQL server unless
explicitly reported in the completion notes.

## Static Files

WhiteNoise is configured through:

- `whitenoise.middleware.WhiteNoiseMiddleware`;
- `whitenoise.storage.CompressedManifestStaticFilesStorage`;
- `STATIC_ROOT=staticfiles`.

Collect static files during release:

```powershell
.\.venv-django52\Scripts\python.exe manage.py collectstatic --noinput
```

`staticfiles/` is generated output and must not be committed.

## Startup Command

Provider-neutral Procfile command:

```text
web: waitress-serve --listen=0.0.0.0:${PORT:-8000} musicplayer.wsgi:application
```

Local development continues to use `runserver`.

## Health And Readiness

- `/health/` confirms the Django process responds and does not query the
  database.
- `/ready/` performs a `SELECT 1` database connectivity query.
- Readiness returns `503` when the database is unavailable.
- Database exception details and credentials are not returned to clients.

## Secure HTTPS Settings

For HTTPS production:

- set `DEBUG=False`;
- use a long non-placeholder `SECRET_KEY`;
- set exact `ALLOWED_HOSTS`;
- use HTTPS `CSRF_TRUSTED_ORIGINS`;
- set `SESSION_COOKIE_SECURE=True`;
- set `CSRF_COOKIE_SECURE=True`;
- enable `SECURE_SSL_REDIRECT=True` only when Django should perform redirects;
- keep `SECURE_HSTS_SECONDS=0` until HTTPS is verified;
- set `TRUST_X_FORWARDED_PROTO=True` only behind a trusted proxy that strips and
  sets `X-Forwarded-Proto` correctly.

## Media Persistence

Local uploads stay under `MEDIA_ROOT=media` for development. Many cloud
platforms use ephemeral app filesystems, so uploaded media is not durable unless
a persistent disk or object storage provider is configured.

During `manage.py test`, Sonica points `MEDIA_ROOT` at a disposable temp
directory so uploaded-file tests do not write into the repository's real local
media folder.

No object storage provider is selected in this phase. Do not deploy or upload
local commercial media. The tracked `media/.gitkeep` remains the only media file
that belongs in Git.

## Deployment Readiness

Run:

```powershell
.\.venv-django52\Scripts\python.exe manage.py check --deploy
.\.venv-django52\Scripts\python.exe manage.py deployment_readiness_check
```

The custom readiness command checks production settings, route resolution,
WhiteNoise configuration, database URL presence when `DEBUG=False`, pending
migrations, and media durability warnings. It does not record secrets.

## Rollback Considerations

Before deploying:

1. Record the release identifier.
2. Back up the production database.
3. Back up uploaded media separately.
4. Record environment variable names and storage locations without values.
5. Confirm migration reversibility before relying on database rollback.

Rollback:

1. Stop or drain traffic.
2. Restore the previous application release.
3. Restore previous environment variable values from the deployment platform.
4. Restore database backup only if the release plan requires data rollback.
5. Restore media storage separately if media changed.
6. Re-run `/health/`, `/ready/`, `check --deploy`, and
   `deployment_readiness_check`.

## Deployment Checklist

- Install dependencies from `requirements.txt`.
- Set safe production environment variables.
- Confirm no secrets are committed.
- Confirm no local media is included.
- Run `check --deploy`.
- Run `deployment_readiness_check`.
- Run `migrate --noinput`.
- Run `collectstatic --noinput`.
- Start Waitress through the platform start command.
- Verify `/health/` and `/ready/`.

## Verification Boundary

Configuration parsing, SQLite fallback, PostgreSQL backend selection,
readiness behavior, deployment checks, migration planning, and static
collection can be verified without a public database.

Actual PostgreSQL connectivity and migration execution require a disposable or
production PostgreSQL instance and must not be claimed unless they are run
against one.
