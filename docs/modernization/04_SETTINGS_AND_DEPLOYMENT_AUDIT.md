# Settings and Deployment Audit

Update: `musicplayer/settings1/` was removed during
`modernization/settings-cleanup`. The findings below are retained as historical
audit evidence from before that cleanup.

## Active Settings Module

`manage.py`, `wsgi.py`, and `asgi.py` default to `musicplayer.settings`.

## Active Environment Variables

- `SECRET_KEY`: required; startup fails if missing.
- `DEBUG`: optional; defaults to `True`.
- `ENABLE_GOOGLE_AUTH`: optional; defaults to `False`.

`.env.example` documents these values.

## Production Gaps

- `DEBUG` defaults to true.
- `ALLOWED_HOSTS` is an empty list and not environment-driven.
- SQLite is the default database.
- No production static-file serving strategy is configured.
- `STATIC_ROOT` is commented out in active settings.
- No `CSRF_TRUSTED_ORIGINS` setting is documented for deployed domains.
- No secure cookie, HSTS, SSL redirect, or proxy SSL settings are configured.
- No production email backend settings are configured.
- No structured `LOGGING` configuration exists.
- Google auth provider configuration relies on database `SocialApp` state.

## Legacy Settings

`musicplayer/settings1/` contains old base/development/production modules.
These are not the default settings path. They reference debug-toolbar and
PostgreSQL configuration but are not verified in the current Project baseline.
The development file is named `developement.py`, which should be treated as a
legacy artifact until intentionally retained or removed.

## SQLite Assumptions

The active app uses SQLite by default. SQLite is suitable for the local
baseline and local demo flow, but production modernization should test:

- PostgreSQL driver installation and settings.
- Case-insensitive uniqueness behavior.
- `distinct()` and string filtering behavior.
- Migration application from a clean database.
- Backup and restore procedures.

## Deployment Modernization Recommendations

1. Split settings into explicit local/test/production modules or a single
   environment-driven module with documented production checks.
2. Make `ALLOWED_HOSTS`, CSRF trusted origins, database URL/parts, and secure
   cookie settings environment-driven.
3. Add a verified static/media story before deployment.
4. Keep `.env` ignored and expand `.env.example` only when settings are added.
5. Remove or quarantine legacy settings after tests prove they are unused.
