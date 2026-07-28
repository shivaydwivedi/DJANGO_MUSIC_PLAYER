# Settings Cleanup

## Authoritative Entry Point

`musicplayer.settings` is the only supported Sonica settings module.

The default entry points all set `DJANGO_SETTINGS_MODULE` to
`musicplayer.settings`:

- `manage.py`
- `musicplayer/wsgi.py`
- `musicplayer/asgi.py`

## Legacy Settings Decision

`musicplayer/settings1/` was removed.

Repository evidence showed it was unused by the supported entry points and
contained stale runtime-looking settings:

- `crispy_forms`, removed during dependency cleanup;
- `debug_toolbar`, removed from the canonical dependency set;
- placeholder PostgreSQL settings, before a PostgreSQL phase exists;
- placeholder production host values;
- duplicate active settings that could confuse the supported entry point.

Historical audit documents may still mention `settings1/` as legacy evidence,
but it is no longer a runtime package.

## Environment Variable Contract

Supported variables:

| Variable | Default | Format | Notes |
| --- | --- | --- | --- |
| `DEBUG` | `True` | `True` or `False` | Keeps local development simple. |
| `SECRET_KEY` | local development placeholder | string | Required when `DEBUG=False`. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1],testserver` | comma-separated hosts | Required when `DEBUG=False`. |
| `CSRF_TRUSTED_ORIGINS` | empty | comma-separated absolute origins | Optional; values must include `http://` or `https://`. |
| `ENABLE_GOOGLE_AUTH` | `False` | `True` or `False` | Shows Google auth only when a real SocialApp is also configured. |

No database environment variables are supported in this phase. Sonica continues
to use local SQLite at `db.sqlite3`.

## Development Defaults

Local development remains one-file simple:

- SQLite database path stays `BASE_DIR / db.sqlite3`.
- Static files continue to load from `static/`.
- Uploaded media continues to use `media/`.
- `DEBUG=True` remains the default.
- local hosts are accepted by default.

## Validation Behavior

Focused validation was added without a new settings framework:

- `SECRET_KEY` must be non-empty when `DEBUG=False`;
- `ALLOWED_HOSTS` must be non-empty when `DEBUG=False`;
- `CSRF_TRUSTED_ORIGINS` values must be absolute `http://` or `https://`
  origins.

Production deployment hardening is still deferred. This phase does not add
secure cookie settings, deployment platform files, PostgreSQL, logging, or
monitoring.

## Tests Added

Settings tests now cover:

- active settings import;
- `manage.py`, WSGI, and ASGI settings defaults;
- absence of the legacy `settings1` runtime package;
- `DEBUG` parsing;
- `ALLOWED_HOSTS` parsing;
- `CSRF_TRUSTED_ORIGINS` parsing and validation;
- production-like rejection of missing `SECRET_KEY`;
- production-like rejection of missing `ALLOWED_HOSTS`;
- local development defaults;
- `ENABLE_GOOGLE_AUTH` parsing;
- absence of crispy/debug-toolbar/Redis/DRF active settings.

## Rollback Instructions

1. Restore `musicplayer/settings1/` from Git only if an older branch explicitly
   depends on it.
2. Revert `musicplayer/settings.py` to the previous environment parsing if the
   new validation blocks a known local workflow.
3. Revert `.env.example`, README, and roadmap documentation updates.

No models or migrations are involved in this cleanup.

## Exact Next Branch

`modernization/production-hardening`

## Exact Next Task

Add production settings hardening for deployed environments while preserving the
current local development defaults.

Update: this follow-up was completed on `modernization/production-hardening`.
