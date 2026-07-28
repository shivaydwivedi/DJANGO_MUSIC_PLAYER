# Sonica Modernization Baseline Audit

## Scope

This audit documents the Sonica Django project as it exists on branch
`modernization/baseline-audit`. It is intentionally read-only for runtime app
behavior: no models, migrations, routes, views, templates, static assets, or
settings were changed.

## Verified Baseline

- Python runtime: Python 3.8.10 in `.\.venv`.
- Django runtime: Django 3.0.8.
- Active settings module: `musicplayer.settings`.
- Project baseline: the project imports, migrations are current, the automated
  suite passes, and the project smoke harness passes.
- Local database/media assumptions: `db.sqlite3` and `media/` are local ignored
  runtime artifacts, not portable project data.

## Current Application Shape

Sonica is a small Django application with two local apps:

- `musicapp`: songs, public browsing, playback routes, favourites, playlists,
  recent-history records, smoke commands, and demo data seeding.
- `authentication`: login, signup, logout, and profile/account pages.

Core public browsing routes remain available without authentication. User-owned
collection pages and mutations are login protected. Playback still records
recent history through explicit GET play routes, which is a known legacy
behavior and the only current GET mutation family.

## High-Confidence Strengths

- The project now has meaningful regression coverage around empty libraries,
  missing media, favourites, playlists, recent history, protected pages, and
  project smoke checks.
- Song media access is guarded in the modernized templates and shared partials.
- Favourites and playlists are scoped to the authenticated user at the view
  layer.
- Google social login is disabled by default through `ENABLE_GOOGLE_AUTH=False`.
- Demo data can be seeded without archived commercial media.

## Primary Modernization Debt

- Django 3.0.8 and Python 3.8.10 are both old; a framework upgrade will require
  careful dependency and API preparation.
- The playlist model stores membership rows directly and has no playlist
  container, which prevents a truly empty named playlist from existing.
- Database integrity relies heavily on view logic because model constraints and
  indexes are missing.
- Upload fields are plain `FileField` values with no size, extension, MIME, or
  content validation.
- Production settings are incomplete and still assume a local SQLite default.
- Logging and observability are minimal.

## Top Five Django Upgrade Blockers

1. `django.utils.http.is_safe_url` is used in `authentication.views`; it was
   replaced by `url_has_allowed_host_and_scheme`.
2. `USE_L10N` remains in active and legacy settings and is removed in newer
   Django versions.
3. `django-allauth==0.42.0` is very old and may require settings, URL, adapter,
   and template compatibility work before a modern Django jump.
4. The dependency set pins old transitive packages such as `asgiref`, `pytz`,
   `sqlparse`, `requests`, `oauthlib`, and `cffi`; some are coupled to old
   Django and allauth behavior.
5. Legacy `settings1/` modules reference PostgreSQL and debug-toolbar setups
   that are not verified against the current dependency/runtime baseline.

## Recommended Next Phase

The next exact phase should be `modernization/django-compat-prep`: replace
deprecated APIs while still running Django 3.0.8, remove or quarantine dead
settings/dependency paths, and add compatibility tests before attempting a
version upgrade.

## Runtime File Change Policy

This phase changed documentation only. Runtime app files should remain
unchanged until a later implementation phase.
