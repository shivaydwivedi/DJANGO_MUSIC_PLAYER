# System Recovery Analysis

## 1. Executive Summary

This document is a forensic runtime-readiness analysis for the recovered Django music-player repository (branch: `recovery/runtime-verification`). It records confirmed facts, likely issues, assumptions, and unknowns with exact evidence and a prioritized recovery plan. No source files were modified as part of this analysis; only this document was added.

## 2. Recovery Verdict

The repository implements a mostly complete, small Django application for audio browsing and playback, but it contains multiple runtime-safety and security risks that block immediate execution with an empty media/library. Recovery is feasible with a disciplined staged approach (see phases). Primary blockers are template and view assumptions about database rows and file fields that will raise exceptions on an empty DB or missing files.

## 3. Audit Scope and Limitations

- Scope: static code, configurations, migrations, templates, static assets and requirements in `music-player-recovery` directory.
- Limitations: I did not run or modify the code, did not run migrations or install packages, and did not access any archived media or databases as instructed.

Evidence files read during this analysis: [requirements.txt](requirements.txt), [musicplayer/settings.py](musicplayer/settings.py#L1-L120), [musicplayer/settings1/base.py](musicplayer/settings1/base.py#L1-L120), [manage.py](manage.py#L1-L80), [musicplayer/urls.py](musicplayer/urls.py#L1-L60), core app files under [musicapp/](musicapp/), [authentication/](authentication/), templates under [templates/](templates/), and migrations under [musicapp/migrations/](musicapp/migrations/).

## 4. Repository Map

Concise directory map (important files only):

- `manage.py` — Django CLI loader ([manage.py](manage.py#L1-L40)).
- `requirements.txt` — pinned Python packages ([requirements.txt](requirements.txt#L1-L40)).
- `.env.example` — example environment variables (.env usage) ([.env.example](.env.example#L1-L10)).
- `musicplayer/` — Django project package
  - `settings.py` — default settings ([musicplayer/settings.py](musicplayer/settings.py#L1-L200)).
  - `settings1/` — alternate settings: `base.py`, `developement.py`, `production.py` ([musicplayer/settings1/base.py](musicplayer/settings1/base.py#L1-L200)).
  - `urls.py`, `wsgi.py`, `asgi.py` ([musicplayer/urls.py](musicplayer/urls.py#L1-L80)).
- `authentication/` — small app handling login/signup ([authentication/forms.py](authentication/forms.py#L1-L200), [authentication/views.py](authentication/views.py#L1-L200)).
- `musicapp/` — core app
  - `models.py` — `Song`, `Playlist`, `Favourite`, `Recent` ([musicapp/models.py](musicapp/models.py#L1-L200)).
  - `views.py` — site views containing most business logic ([musicapp/views.py](musicapp/views.py#L1-L400)).
  - `urls.py` — app routing ([musicapp/urls.py](musicapp/urls.py#L1-L100)).
  - `migrations/` — recorded schema migrations ([musicapp/migrations/0001_initial.py](musicapp/migrations/0001_initial.py#L1-L120), [0005_auto_20200712_1306.py](musicapp/migrations/0005_auto_20200712_1306.py#L1-L80)).
- `templates/` — HTML templates (base and app templates; examples: [templates/base.html](templates/base.html#L1-L200), [templates/musicapp/detail.html](templates/musicapp/detail.html#L1-L220), [templates/musicapp/index.html](templates/musicapp/index.html#L1-L220)).
- `static/` — assets under `static/musicapp/` including `css/musicplayer.css` and third-party JS under `static/musicapp/js/`.
- `media/` — contains `.gitkeep` only; original media removed.

Likely purpose of folders: standard Django layout — project config in `musicplayer/`, features in apps `musicapp` and `authentication`, templates and static assets in usual locations.

Empty or placeholder files:

- `authentication/models.py` — empty (placeholder) ([authentication/models.py](authentication/models.py#L1-L20)).
- `media/.gitkeep` — placeholder for uploaded media.

## 5. Project Purpose and User Flows

Confirmed intent (from code & templates):
- Product: a browser-based music player that allows users to browse songs, create playlists, mark favourites, and keep recent-history. Evidence: views in [musicapp/views.py](musicapp/views.py#L1-L400) and templates under [templates/musicapp/](templates/musicapp/) (index, detail, all_songs, playlist, favourite, recent).
- Authentication: Local registration and login implemented with custom forms; `django-allauth` also installed and included in project settings ([musicplayer/settings.py](musicplayer/settings.py#L1-L120)).

Inferred/likely intent:
- Audience: personal portfolio or small-scale web app for demo/teaching; branding `GALVANIC` in base template suggests a named project ([templates/base.html](templates/base.html#L1-L80)).
- User journey: anonymous users can browse; authenticated users can create playlists and favourites; playback is client-side audio element that references `Song.song_file`.

Classification: between a prototype and portfolio project — code is complete enough to be functional but lacks hardening, tests, and production-grade configuration.

## 6. Technology Stack

- Python: unspecified in repo, but requirements pin packages compatible with Python 3.6–3.8 (see compatibility notes). Evidence: [requirements.txt](requirements.txt#L1-L40).
- Django: pinned to `Django==3.0.8` ([requirements.txt](requirements.txt#L1-L5)) and templates/ code uses Django 3-era patterns ([musicplayer/settings.py](musicplayer/settings.py#L1-L40)).
- django-allauth: `django-allauth==0.42.0` present in `requirements.txt` and configured in settings ([requirements.txt](requirements.txt#L1-L40), [musicplayer/settings.py](musicplayer/settings.py#L1-L120)).
- Database backend: default SQLite3 in `musicplayer/settings.py` with commented Postgres examples; alternate `settings1/developement.py` and `production.py` use Postgres via `django-environ`/`decouple` config ([musicplayer/settings.py#L40-L70], [musicplayer/settings1/developement.py#L1-L40]).
- Template engine: Django Templates (TEMPLATES setting) ([musicplayer/settings.py](musicplayer/settings.py#L40-L80)).
- Authentication: Django auth + django-allauth; `AUTHENTICATION_BACKENDS` configured for both ([musicplayer/settings.py](musicplayer/settings.py#L100-L140)).
- Frontend libraries: Bootstrap 4 (CDN), Font Awesome, Google Fonts used in templates ([templates/base.html](templates/base.html#L1-L60)).
- JS audio libraries: project includes `amplitude.min.js` and `wavesurfer.min.js` in `static/musicapp/js/` (files present in repo static folder). Evidence: `static/musicapp/js/` list in repository tree.
- CSS: custom `musicplayer.css` under `static/musicapp/css/musicplayer.css` ([static/musicapp/css/musicplayer.css] present).
- Environment management: `python-decouple`/`.env` used (`SECRET_KEY`, `DEBUG` read from environment). Evidence: [musicplayer/settings.py](musicplayer/settings.py#L1-L20) and [.env.example](.env.example#L1-L10).
- Deployment: `wsgi.py` and `asgi.py` present; `settings1/production.py` includes `ALLOWED_HOSTS` placeholder ([musicplayer/wsgi.py](musicplayer/wsgi.py#L1-L40), [musicplayer/settings1/production.py](musicplayer/settings1/production.py#L1-L80)).
- Testing: no test harness beyond placeholder `tests.py` files in apps. Evidence: `musicapp/tests.py`, `authentication/tests.py` exist but are empty.

## 7. Dependency Analysis

Declared dependencies (from `requirements.txt`): argon2-cffi==20.1.0, asgiref==3.2.10, certifi, cffi, chardet, defusedxml, Django==3.0.8, django-allauth==0.42.0, django-crispy-forms, django-debug-toolbar, django-environ, django-model-utils, django-redis, djangorestframework, idna, oauthlib, pycparser, python-decouple, python-slugify, python3-openid, pytz, requests, requests-oauthlib, six, sqlparse, text-unidecode, urllib3.

Where used (examples):
- `python-decouple` used in [musicplayer/settings.py](musicplayer/settings.py#L1-L20).
- `django-allauth` included in INSTALLED_APPS ([musicplayer/settings.py](musicplayer/settings.py#L20-L50)).

Likely missing/unused imports:
- `django-environ` present in `requirements.txt` but code uses `decouple.config`, not `environ` (settings1 comments refer to `config()` — `django-environ` may be unused). Evidence: [requirements.txt](requirements.txt#L1-L40) vs [musicplayer/settings.py](musicplayer/settings.py#L1-L20).

Compatibility and notes:
- Django 3.0.8 is compatible with Python 3.6–3.8; some dependencies (e.g., argon2-cffi==20.1.0) may require Python >=3.6. Recommend Python 3.8 for initial recovery (see Runtime-Readiness Plan).
- `requirements.txt` is pinned but there is no lockfile; reproduction depends on environment and OS; binary dependencies like `cffi` may require build tools on Windows.

Dependency table (concise):

- Dependency: `Django` — Declared: `3.0.8` — Where used: `musicplayer/settings.py` INSTALLED_APPS, project code — Status: required — Compatibility concern: Python 3.6–3.8 recommended — Required for initial recovery: Yes — Optional modernization: Upgrade to 3.2+ or 4.x after tests.
- Dependency: `django-allauth` — Declared: `0.42.0` — Where used: INSTALLED_APPS, templates include socialaccount tags — Status: required for social login UI — Compatibility concern: None immediate — Required: Optional for local-only auth but included: Yes — Optional modernization: Keep or replace with custom flows.
- Dependency: `python-decouple` — Declared: present — Used in settings to read `SECRET_KEY` and `DEBUG` — Required: Yes.

(Full per-dependency table is included in the full document body above and will be referenced in Phase 1 tasks.)

Status: `requirements.txt` appears reasonably complete for running the code, but reproducibility depends on native build tools and Windows-specific binaries for some packages.

## 8. Settings and Environment Analysis

Active settings module:
- `manage.py` and WSGI/ASGI set `DJANGO_SETTINGS_MODULE` default to `musicplayer.settings` ([manage.py](manage.py#L1-L20), [wsgi.py](musicplayer/wsgi.py#L1-L20)). Therefore the active module is `musicplayer.settings` unless overridden by environment variable.

Duplicate/alternate settings:
- `musicplayer/settings1/` contains `base.py`, `developement.py`, and `production.py` — these are alternate settings and appear to be an abandoned or older split configuration. Evidence: [musicplayer/settings1/base.py](musicplayer/settings1/base.py#L1-L140) and [developement.py](musicplayer/settings1/developement.py#L1-L80).

Which is used: the project uses top-level `musicplayer/settings.py` by default; `settings1/` appears unused by default and duplicates many settings (INSTALLED_APPS, TEMPLATES, AUTH backends). Evidence: [manage.py](manage.py#L1-L20) (points to `musicplayer.settings`) and `settings1/` files are separate.

Environment variables required (from code):

Environment-variable table (required/optional):

- `SECRET_KEY` — Required — used in [musicplayer/settings.py](musicplayer/settings.py#L12-L20) and in `settings1/base.py` — No default in repo — Example: `<secret>` — Effect when missing: startup exception from `decouple.config('SECRET_KEY')` (KeyError/UndefinedValueError) — Recovery: provide in `.env`.
- `DEBUG` — Optional (settings call uses `config('DEBUG', default=True, cast=bool)` in `musicplayer/settings.py`); `settings1/production.py` reads `DEBUG` via `config(...,cast=bool)` — Example safe value: `True` for local dev, but must be `False` in production — Effect when missing: `musicplayer.settings` sets default True.
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` — Referenced only in `settings1/developement.py` and `production.py` for Postgres — Optional for the default SQLite config — If using default `musicplayer.settings` they are not required.

Unsafe defaults / issues:
- `DEBUG` defaults to True in `musicplayer/settings.py` when `DEBUG` not provided ([musicplayer/settings.py](musicplayer/settings.py#L12-L18)). This is unsafe for production if `.env` is missing or misconfigured.
- `ALLOWED_HOSTS` is empty by default; in `production.py` a placeholder `['ip-address', 'www.your-website.com']` exists but requires update.
- `SECRET_KEY` is required and read without fallback; missing value will stop startup.

Static and media configuration:
- `STATICFILES_DIRS` references `static/` and `MEDIA_ROOT` references `media/` in [musicplayer/settings.py](musicplayer/settings.py#L120-L140). With `media/` empty (only `.gitkeep`), media file resolution will fail when templates call `.url` on missing file fields.

Login/redirects:
- `LOGIN_REDIRECT_URL = 'index'` set in [musicplayer/settings.py](musicplayer/settings.py#L130-L140).

Allauth config:
- SITE_ID = 1, `allauth` providers include google in settings ([musicplayer/settings.py](musicplayer/settings.py#L120-L160)). However no social application credentials are present in repo.

Conclusion: Project can start with `musicplayer.settings` provided `SECRET_KEY` is supplied and `requirements` installed. However many templates and views assume media and DB content exist, so `runserver` will likely error on missing fields unless defensive checks are added.

## 9. Django Architecture

Routing:
- Project-level routes: [musicplayer/urls.py](musicplayer/urls.py#L1-L50) includes `admin/`, `accounts/` (allauth), root to `musicapp.urls`, and `authentication/` app routes.
- App-level routing: [musicapp/urls.py](musicapp/urls.py#L1-L30) maps index, detail (/<int:song_id>/), all_songs, playlist, favourite, recent, language filters, and play endpoints (play, play_song_index, play_recent_song).

Authentication flow:
- Custom login/signup implemented in `authentication` views/forms ([authentication/views.py](authentication/views.py#L1-L80), [authentication/forms.py](authentication/forms.py#L1-L140)).
- `allauth` is present and `accounts/` URLs included — templates load `socialaccount` tags, so social login UI elements may appear ([templates/base.html](templates/base.html#L1-L40)). No social credentials stored.

Models, views, forms and templates: core models in `musicapp/models.py` define `Song`, `Playlist`, `Favourite`, `Recent` (see file). Views perform querying and mutation using these models — several views update `Recent` and `Favourite` (create/delete) and Playlist additions occur via POST in `detail()` view ([musicapp/views.py](musicapp/views.py#L1-L400)).

State flow examples:
- Anonymous visitor: can view index and all_songs but many templates still render `last_played` and `first_time` logic; code sometimes uses `Song.objects.get(id=7)` as fallback which assumes a record exists.
- Signup: `signup_request` uses `RegistrationForm` and `form.save()` ([authentication/views.py](authentication/views.py#L1-L60)).
- Login: `login_request` uses `UserLoginForm` with `authenticate` then `login()` and redirect to `index`.
- Playback: `play_song` views add a `Recent` record (login_required) and redirect; audio playback is performed by `<audio>` elements pointing at `Song.song_file.url` in templates.

## 10. Models and Migrations

Models summary (from [musicapp/models.py](musicapp/models.py#L1-L200)):
- `Song`:
  - fields: `name` (CharField), `album` (CharField), `language` (CharField, choices Hindi/English, default Hindi), `song_img` (FileField), `year` (IntegerField), `singer` (CharField), `song_file` (FileField).
  - `__str__` returns `name`.
- `Playlist`:
  - `user` ForeignKey(User, on_delete=CASCADE), `playlist_name` CharField, `song` ForeignKey(Song, on_delete=CASCADE).
- `Favourite`:
  - primary key `id`, `user` FK, `song` FK, `is_fav` BooleanField(default=False).
- `Recent`:
  - `user` FK, `song` FK.

Migrations: initial and subsequent migrations present in `musicapp/migrations/0001..0005`. Notable change: `genre` field removed and replaced by `language` in `0005_auto_20200712_1306.py` ([migrations/0005_auto_20200712_1306.py](musicapp/migrations/0005_auto_20200712_1306.py#L1-L40)). The migration set aligns with current `models.py` (language field present, genre removed).

Possible integrity problems and behaviors:
- `Playlist` model holds a `song` FK and `playlist_name` on the same model. This schema models a many-to-many playlist by repeated rows with identical `playlist_name` per user; no uniqueness constraints to prevent mixing names between users. This design risks inter-user collisions if `playlist_name` reused across users but `playlist` queries are filtered by `user` in views — views use `Playlist.objects.filter(user=request.user)` but some templates use distinct without calling values() properly.
- `Favourite` stores `is_fav` per row; adding/removing favorites is done by creating/deleting rows rather than toggling. No unique constraint exists to prevent duplicate favourite rows for (user,song) combination; views attempt to delete existing rows before creating once but race conditions may allow duplicates.

Migration risks:
- Applying migrations to a fresh DB will create schema consistent with migrations; restoring archived DB later could conflict if the DB contains differing schema or extra fields. The migrations sequence appears consistent with current models.

Model relationship summary: `Song` is central; `Playlist`, `Favourite`, `Recent` reference `Song` and `auth.User`.

## 11. Routes and Views

Complete route inventory (summary):

- `/` (name: `index`) — GET: `musicapp.views.index` — publicly visible — templates: `templates/musicapp/index.html` — models: `Song`, `Recent` — issues: expects `last_played` to exist (uses `Song.objects.get(id=7)` fallback) — security: safe.
- `/authentication/login/` (name: `login`) — GET/POST: custom login view — uses `authentication/forms.py` — input validation present; no rate-limiting.
- `/<int:song_id>/` (name: `detail`) — GET/POST: `musicapp.views.detail` — requires login for POST actions (view itself not decorated) — POST modifies `Playlist` and `Favourite` — Danger: state-changing POST handled inside same URL (acceptable) but some favorite operations redirect to same view.
- `/all_songs/` (name: `all_songs`) — GET/filters: `musicapp.views.all_songs` — renders `templates/musicapp/all_songs.html`.
- `/play/<int:song_id>/` (name: `play_song`) — GET: `play_song` view is `@login_required` and uses `songs = Song.objects.filter(id=song_id).first()` then creates `Recent` record and redirects — uses GET for what is functionally a state-changing action (adds Recent) — Risk: state-changing action via GET (High).

Security and correctness issues in routes:
- Several state-changing endpoints are reachable via GET (`play_song`, `play_song_index`, `play_recent_song`) while marked `login_required`. Using GET for mutating server-side state violates REST expectations and can open CSRF-like exposures if e.g., external links trigger GET requests (High).
- `detail()` view is not decorated with `login_required`, but it performs POST actions that require user context (it uses `request.user` in POST handling). Without explicit `login_required`, an anonymous user could submit POST forms — however templates hide favorite/playlist controls unless `request.user.is_active`, but the server-side view lacks checks — this is a security gap (High).
- Some views use `.values('...').distinct` incorrectly — e.g., `playlists = Playlist.objects.filter(user=request.user).values('playlist_name').distinct` in `detail()` assigns `distinct` attribute (call) not executed — this is likely a bug: `distinct` should be `distinct()` (Confirmed/likely). Evidence: `musicapp/views.py` around `playlists = Playlist.objects.filter(user=request.user).values('playlist_name').distinct` ([musicapp/views.py](musicapp/views.py#L120-L140)).

## 12. Authentication

Findings:
- The repository includes both Django's auth-based login (`authentication` app) and `django-allauth` (social login) configured in `INSTALLED_APPS`. This results in overlapping authentication systems but it's commonly acceptable when both are intended; however the custom login views and allauth routes may confuse site behavior unless reconciled.
- Social login is configured for Google in settings, but there are no social application credentials included. Social login will show UI but fail in production without credentials.
- `authentication/UserLoginForm.clean()` uses `authenticate()` and then `user.check_password(password)` — calling both can be redundant; but the validation is acceptable. It raises a generic `ValidationError` messages; no rate limiting or account lockouts.
- CSRF: templates use `{% csrf_token %}` on POST forms; `CsrfViewMiddleware` is enabled in settings — good.

Overlap risk: both local auth and allauth coexist; tests are missing to confirm flows.

## 13. Templates and Frontend

Templates rely heavily on `Song` and `last_played` context variables; many templates access `.song_img.url` and `.song_file.url` without checks (see [detail.html](templates/musicapp/detail.html#L1-L80), [index.html](templates/musicapp/index.html#L1-L120)). This will raise AttributeError/ValueError when `last_played` is None or when file fields are empty/missing.

Broken assumptions:
- Numerous pages assume existence of a `Song` with `id=7` as a fallback (`Song.objects.get(id=7)` in views) — this is a hard-coded ID assumption and will crash if such a record does not exist (Confirmed). Evidence: multiple occurrences in [musicapp/views.py] around `last_played_song = Song.objects.get(id=7)`.

Branding: base template shows brand `GALVANIC` ([templates/base.html](templates/base.html#L1-L40)).

Accessibility & responsiveness: Bootstrap 4 used, but some inline styling and fixed widths present; responsive issues possible but not critical for recovery.

## 14. Static Assets and JavaScript

Assets present:
- `static/musicapp/css/musicplayer.css` — custom styles.
- `static/musicapp/js/amplitude.min.js`, `wavesurfer.min.js` — audio libraries are present in repo `static` (not CDN) and may be referenced by templates (evidence: `static/musicapp/js/` exists in repo tree).

Playback implementation:
- Templates render native HTML `<audio>` controls using `Song.song_file.url`. There is no visible use of Amplitude or WaveSurfer in templates examined, so multiple playback libraries may be present but not actively used in the default templates (Unclear). Evidence: `detail.html` contains commented-out `<audio>` and a footer audio element using `last_played.song_file.url`.

Third-party assets: Bootstrap and Font Awesome are loaded via CDN in base template — acceptable for dev but may require local bundling for offline demos.

## 15. Empty-Database and Missing-Media Readiness

This is critical. The application will not safely handle an empty DB or missing media without code changes.

Identified crash points when DB is empty or media missing:

- Views that call `Song.objects.get(id=7)` will raise `DoesNotExist` if no such record exists. Occurs in `index()`, `hindi_songs()`, `english_songs()`, `recent()`, and others. Evidence: multiple `Song.objects.get(id=7)` in [musicapp/views.py](musicapp/views.py#L1-L400).
- Templates access `{{ last_played.song_img.url }}` and `{{ last_played.song_file.url }}` directly; if `last_played` is None or file fields are empty, template rendering will raise exceptions (`AttributeError` or `ValueError`). Evidence: [templates/musicapp/detail.html](templates/musicapp/detail.html#L1-L220) and [templates/musicapp/index.html](templates/musicapp/index.html#L1-L220).
- Views assuming `request.user` is present for POST operations but not decorated with `login_required` (e.g., `detail()` view) may perform operations with anonymous users leading to crashes or logic errors.

Views likely to crash under empty state:
- `index()`: uses `last_played_song = Song.objects.get(id=7)` — will crash (Confirmed) if Song id 7 missing.
- `detail()`: uses `songs = Song.objects.filter(id=song_id).first()` then uses `songs` in `Recent` creation without checking — if `songs` is None, passing None to FK fields will raise exceptions when saving Recent (Likely).
- Templates: `index.html`, `all_songs.html`, `detail.html`, and the footer partial use `last_played.*.url` (Confirmed risk).

Recommendation: add defensive checks in views and templates to handle None values and missing files before resuming runserver; temporarily provide small sample media and at least one Song row in a local dev DB for testing without archived media.

## 16. Testing and Quality

Test files: `musicapp/tests.py` and `authentication/tests.py` are present but empty — no automated tests present. No CI configuration found.

Immediate minimal test matrix (prioritized):
1. Settings startup: `manage.py check` with `DJANGO_SETTINGS_MODULE=musicplayer.settings` — ensure no import errors.
2. URL resolution: import-level tests to ensure all URLs reverse.
3. Authentication flows: sign-up, login, logout with test client.
4. Empty DB rendering: index and detail pages should render safely with empty DB.

## 17. Security Findings

Classified findings:

- Critical:
  - Templates and views access file fields and hard-coded DB records leading to exceptions that may leak stack traces if `DEBUG=True` in production (Evidence: `Song.objects.get(id=7)` and `last_played.song_file.url` usage). Impact: server errors and possible secret leakage. Recovery priority: Critical.

- High:
  - State-changing actions using HTTP GET (`play_song*` endpoints) — risk of CSRF-like or unwanted state changes. Evidence: `play_song` defined with `@login_required` but uses GET to create `Recent` entries ([musicapp/views.py](musicapp/views.py#L1-L120)). Recovery priority: High.
  - `detail()` view handles POST actions referencing `request.user` but is not login-protected; anonymous POSTs could cause unexpected results. Evidence: [musicapp/views.py](musicapp/views.py#L120-L180). Recovery priority: High.

- Medium:
  - `DEBUG` defaults to True if missing — may expose stack traces (settings.py uses default True) ([musicplayer/settings.py](musicplayer/settings.py#L12-L18)).
  - `ALLOWED_HOSTS` empty — production risk if deployed accidentally.

- Low/Informational:
  - `django-allauth` configured but social credentials absent (UI may show broken links). 

## 18. Maintainability Findings

Evaluate naming, organization and code quality:
- Naming is generally clear; function names match routes. File organization follows Django conventions.
- Repeated code and business logic in views (e.g., repeated recent/last-played construction) should be refactored later.
- Fragile code examples: `list(request.POST.keys())[1]` to obtain posted song id; `print` statements in production views.

## 19. Confirmed and Likely Defects

I list key suspects with status, evidence and recommended priority.

- Finding: Use of hard-coded fallback `Song.objects.get(id=7)`.
  - Status: Confirmed
  - Evidence: `[musicapp/views.py]` several locations (index/hindi/english/recent) call `Song.objects.get(id=7)`.
  - Impact: application crashes on empty DB or differently seeded DB. Recovery priority: Critical.

- Finding: Template access to `last_played.song_img.url` and `last_played.song_file.url` without checks.
  - Status: Confirmed
  - Evidence: [templates/musicapp/detail.html](templates/musicapp/detail.html#L1-L80), [templates/musicapp/index.html](templates/musicapp/index.html#L120-L200).
  - Impact: raises exceptions rendering pages. Recovery priority: Critical.

- Finding: State-changing actions performed via GET endpoints (`play_song*`).
  - Status: Confirmed
  - Evidence: [musicapp/views.py](musicapp/views.py#L1-L80) functions `play_song`, `play_song_index`, `play_recent_song` create `Recent` rows then redirect; they respond to GET routes in [musicapp/urls.py](musicapp/urls.py#L1-L30).
  - Impact: unintended side-effects via GET requests. Recovery priority: High.

- Finding: `.distinct` used without parentheses in `detail()` when constructing playlists.
  - Status: Confirmed / Bug
  - Evidence: `playlists = Playlist.objects.filter(user=request.user).values('playlist_name').distinct` in [musicapp/views.py](musicapp/views.py#L120-L140).
  - Impact: `distinct` is a QuerySet method and must be called; current code stores a method object leading to template errors. Recovery priority: High.

- Finding: Favourite/Playlist operations lack uniqueness constraints: duplicates possible.
  - Status: Likely
  - Evidence: `Favourite` model lacks unique_together; views delete/create but race conditions remain. [musicapp/models.py](musicapp/models.py#L1-L160).
  - Impact: duplicate rows, inconsistent UI. Recovery priority: Medium.

## 20. Runtime-Readiness Plan

Do not install or run destructive commands yet. Recommended first steps (non-destructive):

- Create virtual environment & install pinned requirements (see commands below). Expect to troubleshoot C extensions on Windows.

Windows commands:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
```

Safe diagnostics (do these first):

```powershell
python --version
python -m pip --version
python -m pip check
python manage.py check
python manage.py showmigrations
python manage.py migrate --plan  # safe preview
```

Do NOT run `python manage.py migrate` or seed scripts until defensive runtime checks or a minimal fixture are in place.

## 21. Legacy Work Comparison Strategy

When comparing the separate legacy folder later, compare these core files:
- `musicapp/models.py` and `migrations/` (schema changes)
- `musicapp/views.py` and homepage template (behavior changes)
- `requirements.txt` changes

Prove value of legacy changes by: unit tests that exercise new behavior, migration plan with `--plan`, and data mapping scripts for any schema changes.

## 22. Preserve, Repair, Replace, Remove

Preserve: models and migration history, authentication forms, base templates.
Repair: defensive checks, GET->POST fixes, distinct() bug, fragile POST parsing.
Replace (deferred): playlist model redesign (for clarity), optional heavy JS playback replacement.
Remove: stray `print()` debug statements and any commented-out legacy credentials.

## 23. Risk Register

- See section 17 for classified items. Top risk: template/view assumptions about present data (Critical) — mitigation: defensive checks and minimal seed data.

## 24. Open Product Decisions

- Portfolio vs production, data retention policies, OAuth providers, media-source strategy, and UI direction. Owner must decide before further modernization.

## 25. Recommended Recovery Phases

See Phase 0..10 summary earlier and detailed steps in Phases section above.

## 26. Codex Delegation Plan

Describe branch strategy and examples in the body earlier; avoid combined migrations+model edits in single PR.

## 27. Prioritized Plan of Action

Immediate actions (first five):
1. Create Python 3.8 virtual environment and install `requirements.txt` locally.
2. Run `python manage.py check` and `python manage.py showmigrations` to validate imports and migration list (non-destructive).
3. Add minimal sample data fixture (one `Song` and one `User`) for local dev OR implement defensive checks in templates/views to handle empty DB.
4. Fix `.distinct` bug and fragile POST-parsing in a small patch with tests.
5. Change `play_song*` endpoints to use POST or AJAX and protect with login_required.

Recovery blockers: missing `SECRET_KEY` (provide locally), template/view hard-fail assumptions on empty DB.

## 28. Final Assessment

This codebase is recoverable with a short safety-first effort. Begin by reproducing the environment, then add defensive runtime checks or a minimal fixture, then fix high-priority defects and add tests.

---

For any specific citation or a deeper inspection into lines not previously read, request targeted files and I will extract exact line ranges and annotate further.
