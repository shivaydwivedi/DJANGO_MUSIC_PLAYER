# Deployment Readiness

## Current Status

Sonica is ready for platform selection and deployment rehearsal, but it is not
yet public-production ready. The project has a supported Django 5.2 runtime,
environment-driven security settings, error templates, health/readiness probes,
and a production WSGI server dependency. No hosting provider has been selected.

## Production Server Decision

Selected server: Waitress `3.0.2`.

Waitress was chosen because it is a production WSGI server, imports cleanly in
the current Windows development environment, is usable on Linux deployments, and
serves the existing synchronous Django WSGI app without introducing ASGI or
websocket assumptions.

Production application entry point:

```text
musicplayer.wsgi:application
```

Production start command:

```powershell
.\.venv-django52\Scripts\waitress-serve.exe --listen=0.0.0.0:8000 musicplayer.wsgi:application
```

Local development still uses:

```powershell
.\.venv-django52\Scripts\python.exe manage.py runserver
```

## Startup And Release Sequence

Platform-neutral release order:

1. Install dependencies:

   ```powershell
   .\.venv-django52\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Set environment variables in the deployment environment.

3. Run deployment checks:

   ```powershell
   .\.venv-django52\Scripts\python.exe manage.py check --deploy
   .\.venv-django52\Scripts\python.exe manage.py deployment_readiness_check
   ```

4. Apply migrations:

   ```powershell
   .\.venv-django52\Scripts\python.exe manage.py migrate --noinput
   ```

5. Collect static files:

   ```powershell
   .\.venv-django52\Scripts\python.exe manage.py collectstatic --noinput
   ```

6. Start the production WSGI server.

## Environment Variable Contract

| Variable | Required? | Local default | Production recommendation | Format | Risk if misconfigured |
| --- | --- | --- | --- | --- | --- |
| `DEBUG` | optional | `True` | `False` | boolean | `True` exposes debug details. |
| `SECRET_KEY` | production yes | local fallback | long random secret | string | Weak secrets break signing security. |
| `ALLOWED_HOSTS` | production yes | local hosts | exact domains | comma-separated hosts | Empty fails; wildcard weakens host protection. |
| `CSRF_TRUSTED_ORIGINS` | optional | empty | HTTPS deployment origins if needed | comma-separated origins | Bad origins can break or weaken CSRF protection. |
| `ENABLE_GOOGLE_AUTH` | optional | `False` | only true with real SocialApp | boolean | True alone does not configure OAuth. |
| `SECURE_SSL_REDIRECT` | optional | `False` | `True` unless proxy redirects | boolean | HTTP traffic may stay unencrypted. |
| `SESSION_COOKIE_SECURE` | optional | `False` | `True` | boolean | Session cookie can travel over HTTP. |
| `CSRF_COOKIE_SECURE` | optional | `False` | `True` | boolean | CSRF cookie can travel over HTTP. |
| `SECURE_HSTS_SECONDS` | optional | `0` | staged positive value after HTTPS verification | non-negative integer | Careless HSTS can lock clients into broken HTTPS. |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | optional | `False` | only after subdomain audit | boolean | Can affect all subdomains. |
| `SECURE_HSTS_PRELOAD` | optional | `False` | only after preload readiness | boolean | Difficult to reverse once submitted. |
| `SECURE_CONTENT_TYPE_NOSNIFF` | optional | `True` | `True` | boolean | Browser may sniff content types. |
| `SECURE_REFERRER_POLICY` | optional | `strict-origin-when-cross-origin` | keep or tighten by policy | string | May leak too much referrer data. |
| `X_FRAME_OPTIONS` | optional | `DENY` | `DENY` | string | Weak setting can allow clickjacking. |
| `SESSION_COOKIE_HTTPONLY` | not env-driven | `True` | `True` | boolean setting | JavaScript could access session cookie if false. |
| `SESSION_COOKIE_SAMESITE` | optional | `Lax` | `Lax` unless integration requires otherwise | string | Bad value can break auth flows or weaken CSRF posture. |
| `CSRF_COOKIE_SAMESITE` | optional | `Lax` | `Lax` unless integration requires otherwise | string | Bad value can break forms or weaken CSRF posture. |
| `TRUST_X_FORWARDED_PROTO` | optional | `False` | true only behind trusted proxy | boolean | Header spoofing can confuse HTTPS detection. |
| `USE_X_FORWARDED_HOST` | optional | `False` | false unless proxy contract requires it | boolean | Header spoofing can affect host handling. |

## Health And Readiness

`/health/`:

- anonymous;
- safe methods only;
- returns `{"status": "ok"}`;
- performs no database query;
- exposes no secrets, versions, paths, or environment details.

`/ready/`:

- anonymous;
- safe methods only;
- performs one `SELECT 1` database connectivity query;
- returns `{"status": "ok"}` on success;
- returns `503` with `{"status": "unavailable"}` on database failure;
- does not expose database errors or credentials.

## Static Files

Source static files live in `static/`.

Collected static output goes to `STATIC_ROOT=staticfiles`, which is separate
from source static directories. `collectstatic --dry-run` succeeds. Collected
files are not committed.

Django serves static files only in development through `DEBUG=True` URL helpers.
In production, the deployment platform, reverse proxy, or static-file service
must serve collected files. WhiteNoise was not added in this phase.

## Uploaded Media

Local uploaded media lives under `MEDIA_ROOT=media` and is served by Django only
in development. Public deployment needs persistent media storage before users
can rely on uploads.

Ephemeral deployment disks are unsafe for permanent media. Database backups do
not include uploaded files. Media backup, migration, and restore procedures are
separate deployment concerns.

## Database Strategy

SQLite remains the active database for local development and controlled demo
use. It is file-based, assumes a single writable instance, has write concurrency
limits, and is unsafe on ephemeral filesystems without explicit backup/restore
handling.

PostgreSQL is required before multi-user or horizontally scaled production
deployment.

Exact future branch:

```text
modernization/postgresql
```

## Google Authentication

Google authentication remains disabled by default. `ENABLE_GOOGLE_AUTH=True` is
not enough by itself. A valid Django `SocialApp` must exist for the deployed
site, and client ID/secret values must live outside the repository.

Callback URLs, JavaScript origins, and OAuth consent configuration are
deployment-domain-specific. Local username/password authentication remains
available without Google.

## Deployment Readiness Command

Added:

```powershell
.\.venv-django52\Scripts\python.exe manage.py deployment_readiness_check
```

The command is non-destructive. It verifies `DEBUG=False`, allowed hosts,
`STATIC_ROOT`, `MEDIA_ROOT`, health/readiness URL resolution, Django deployment
checks, and absence of pending migrations. It prints PASS/FAIL without secrets
and exits non-zero on failure.

## Backup Plan

Before each release:

1. Snapshot environment variable names and configuration source locations
   without recording secret values.
2. Back up the database before running migrations.
3. Back up uploaded media separately from the database.
4. Record the application release identifier.
5. Treat static assets as rebuildable from source plus dependencies.

Do not assume all migrations are reversible until reviewed.

## Rollback Plan

1. Stop or drain traffic to the failing release.
2. Restore the previous application release.
3. Restore environment variables from the previous deployment configuration
   source without committing values.
4. Review migration reversibility before rolling the database back.
5. Restore database backup only if the release plan calls for data rollback.
6. Restore media backup separately if media changed.
7. Re-run `check --deploy`, `deployment_readiness_check`, `/health/`, and
   `/ready/`.

## Unresolved Blockers

- No hosting provider selected.
- PostgreSQL support is not implemented.
- Persistent uploaded-media storage is not implemented.
- Static serving is delegated to the future platform/reverse proxy.
- OAuth production credentials and domain configuration are not set.
- No CI/CD, Docker, Redis, or external monitoring is configured.

## Exact Next Branch

`modernization/postgresql`

## Exact Next Task

Add PostgreSQL configuration support and migration rehearsal while preserving
SQLite for local development.
