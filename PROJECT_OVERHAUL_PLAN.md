# Project Overhaul Plan

## 1. Executive Summary

The project is feasible to overhaul, but not safely through a full rewrite as the first move. The current repository contains a small, coherent Django music-player application with useful domain concepts, templates, routes, and migrations, but runtime verification is blocked before Django startup because the active environment only exposes Python 3.14.6 while the dependency set is Django 3.0-era. The first implementation work must remain recovery-focused until the old behavior is reproducible and covered by tests.

Recommended direction:

- Recover the inherited Django app first on a compatible runtime.
- Add a baseline regression suite before schema, dependency, or UI modernization.
- Target a modern Django monolith for version 1, with server-rendered templates and optional HTMX/Alpine for progressive interactions.
- Use PostgreSQL in production after SQLite recovery is proven locally.
- Keep media admin-managed for version 1 with only original, public-domain, openly licensed, or authorized demo files.
- Defer a separate React frontend, APIs, cloud uploads, background jobs, recommendation systems, and streaming-platform features until there is a concrete need.

Primary recommendation:

* **Recommendation:** Build Scope 2, "Modern Music Library", using a modern Django monolith with room for HTMX-enhanced interactions.
* **Classification:** Required overhaul
* **Evidence:** `musicapp/models.py` already has `Song`, `Playlist`, `Favourite`, and `Recent`; `musicapp/urls.py` exposes browsing, history, playlist, favourite, and playback routes; templates under `templates/musicapp/` already implement those pages; `requirements.txt` pins Django 3.0.8 and old supporting packages; `RUNTIME_VERIFICATION_REPORT.md` shows startup is blocked before Django import.
* **Reasoning:** The inherited app has enough product shape to recover and modernize incrementally. A full SPA/API split would add deployment, authentication, and test complexity before the current backend behavior is understood.
* **Benefits:** Faster stabilization, less architectural risk, clear portfolio story, fewer moving parts, easier deployment.
* **Risks:** Old code may hide runtime defects until dependencies install; model redesign requires careful migrations; UI rewrite can grow in scope.
* **Dependencies:** Compatible Python runtime, dependency restoration, empty-state fixes, baseline tests.
* **Relative effort:** Large
* **Approval required:** Yes
* **Verification method:** Passing Django checks, migration dry-runs, full test suite, browser smoke tests, production deployment smoke test.

## 2. Current-System Baseline

Repository root:

- The active Django repository is `C:\Users\polma\Desktop\django_music_player\music-player-recovery`, not the outer workspace folder. Evidence: `RUNTIME_VERIFICATION_REPORT.md` section 1 and the presence of `manage.py`, `musicplayer/`, `musicapp/`, `authentication/`, `templates/`, and `static/` in that directory.

Active settings module:

- `manage.py` sets `DJANGO_SETTINGS_MODULE` to `musicplayer.settings`.
- `musicplayer/wsgi.py` and `musicplayer/asgi.py` are present for deployment entrypoints.
- `musicplayer/settings1/` contains alternate split settings, but the default command path does not use them.

Applications:

- `authentication/`: custom login, signup, logout forms and views.
- `musicapp/`: domain app for songs, playlists, favourites, recent history, browsing, playback routes, and admin registration.
- Django contrib apps and django-allauth apps are listed in `musicplayer/settings.py`.

Models:

- `Song`: `name`, `album`, `language`, `song_img`, `year`, `singer`, `song_file`.
- `Playlist`: `user`, `playlist_name`, `song`.
- `Favourite`: `user`, `song`, `is_fav`.
- `Recent`: `user`, `song`.
- Evidence: `musicapp/models.py`.

Routes:

- Project routes: `admin/`, `accounts/`, root include for `musicapp.urls`, and `authentication/`. Evidence: `musicplayer/urls.py`.
- App routes: index, detail, mymusic, playlist, playlist songs, favourite, all songs, recent, Hindi songs, English songs, and three playback-history routes. Evidence: `musicapp/urls.py`.
- Auth routes: login, signup, logout. Evidence: `authentication/urls.py`.

Views:

- `musicapp/views.py` provides function-based views for browsing, search, detail, favourites, playlists, and playback history.
- Confirmed risks include hardcoded `Song.objects.get(id=7)` at lines reported by `Select-String`, `.distinct` referenced without calling it in playlist contexts, fragile `list(request.POST.keys())[1]`, and debug `print()` calls.
- `detail()`, `play_song()`, `play_song_index()`, and `play_recent_song()` mutate recent-history state; playback routes are GET routes.

Templates:

- Server-rendered Django templates are under `templates/base.html`, `templates/musicapp/*.html`, and `templates/authentication/*.html`.
- Templates use Bootstrap 4 CDN, Font Awesome 4 CDN, Google Fonts, crispy forms, and direct native `<audio>` tags.
- Direct media references include `song.song_img.url`, `last_played.song_img.url`, `song.song_file.url`, and `last_played.song_file.url`. Evidence: `Select-String` results for `templates/musicapp/*.html`.

Authentication systems:

- Custom local auth exists in `authentication/forms.py` and `authentication/views.py`.
- django-allauth is configured in `musicplayer/settings.py` and mounted at `accounts/`.
- Google social login buttons are rendered in `templates/authentication/login.html` and `templates/authentication/signup.html`.
- `ACCOUNT_EMAIL_VERIFICATION = 'none'`.

Static assets and JavaScript:

- Custom CSS is in `static/musicapp/css/musicplayer.css`.
- Bundled JS libraries include `static/musicapp/js/amplitude.min.js` and `static/musicapp/js/wavesurfer.min.js`.
- Current templates observed use native `<audio>` tags; no confirmed active use of Amplitude or WaveSurfer was found in templates.
- Static image `static/musicapp/images/bg.jpg` is used as a playlist thumbnail.

Dependencies:

- `requirements.txt` pins Django 3.0.8, django-allauth 0.42.0, django-crispy-forms 1.9.1, django-debug-toolbar 2.2, djangorestframework 3.11.0, django-redis 4.12.1, django-environ 0.4.5, python-decouple 3.3, and old request/oauth packages.
- Runtime verification shows unchanged installation fails on Python 3.14.6 at `django-allauth==0.42.0`.

Migrations:

- `musicapp/migrations/0001_initial.py` creates `Song` with `genre`.
- `0002_playlist.py`, `0003_favourite.py`, and `0004_recent.py` create user-song relationship models.
- `0005_auto_20200712_1306.py` removes `genre` and adds `language`.

Tests:

- `musicapp/tests.py` and `authentication/tests.py` exist but contain no meaningful tests.
- No CI configuration was found in `rg --files`.

Deployment readiness:

- Not production-ready. `musicplayer/settings.py` has `DEBUG` defaulting to true, empty `ALLOWED_HOSTS`, no active `STATIC_ROOT`, SQLite default database, no production server config, no CI, and no tested deployment path.
- `musicplayer/settings1/production.py` contains placeholder `ALLOWED_HOSTS` and PostgreSQL settings, but it is not the active settings module.

Runtime status:

- Blocked before Django startup. Django is not installed because dependency installation did not complete. Evidence: `RUNTIME_VERIFICATION_REPORT.md`.

## 3. Recovery Versus Overhaul Boundary

Recovery work makes the inherited application function safely without changing product identity.

Recovery includes:

- Install a compatible Python runtime and reproduce old dependencies.
- Make Django import, settings load, and management checks run.
- Run migration discovery and create a disposable local database only after reviewed migration plans.
- Remove hardcoded fallback song IDs.
- Make empty song libraries and missing media safe.
- Fix `.distinct` call bugs.
- Replace fragile POST parsing with explicit form fields.
- Remove debug prints.
- Require login and POST for user-specific mutations.
- Define and repair current recent-history behavior.
- Add tests for existing behavior.
- Document current behavior and setup.

Overhaul work intentionally changes architecture, product behavior, data model, UI, or operational posture.

Overhaul includes:

- Django and Python upgrades after tests exist.
- Normalized playlist schema.
- Favourite uniqueness constraints.
- Listening history timestamps and play events.
- New search/filtering behavior.
- User profile support.
- Responsive UI redesign and branding replacement.
- Production PostgreSQL.
- Deployment configuration.
- CI and security scanning.
- Optional HTMX/Alpine interactions.
- Optional API only after an API consumer is identified.
- Optional cloud storage only after deployment and media decisions are made.

Boundary rule:

- Do not mix recovery and overhaul in the same branch. Recovery branches should prove existing behavior. Overhaul branches may change behavior only after tests define the recovered baseline.

## 4. Recommended Target Product

Recommended product scope: Scope 2, "Modern Music Library".

This should be a polished portfolio-quality Django music-library app, not a broad streaming platform. Version 1 should support secure accounts, admin-managed legal demo songs, browsing, search, playlists, favourites, recent history, play counts, trending songs, user profiles, empty states, tests, CI, and a deployable production setup.

* **Recommendation:** Build a modern music-library portfolio product rather than a streaming platform.
* **Classification:** Required overhaul
* **Evidence:** Current app already supports local users, songs, search, playlists, favourites, recent history, and playback through `musicapp/views.py`, `authentication/views.py`, and `templates/musicapp/*.html`.
* **Reasoning:** This scope extends the existing product identity without forcing uploads, moderation, signed URLs, transcoding, or separate clients.
* **Benefits:** Strong portfolio value, clear recovery story, manageable complexity.
* **Risks:** Still requires schema changes, UI redesign, tests, deployment, and legal media policy.
* **Dependencies:** Recovery baseline, product decisions for media and auth.
* **Relative effort:** Large
* **Approval required:** Yes
* **Verification method:** Complete test suite, legal demo media verification, deployed smoke test.

## 5. Recommended Target Architecture

Primary architecture: Modern Django monolith.

- Django templates remain the first-class rendering layer.
- Django forms handle validation.
- Bootstrap 5 or a small custom CSS system can replace Bootstrap 4 after UI decisions.
- HTMX may be introduced selectively for playlist/favourite/player interactions if it reduces full-page reload friction.
- PostgreSQL is used in production.
- SQLite remains acceptable for disposable local recovery.
- Static files handled with WhiteNoise or platform static hosting.
- Media stored locally for development; production media strategy selected before deployment.

Fallback architecture: Django plus HTMX/Alpine.

- Use this when richer interactions are needed but a separate SPA is still unjustified.
- Keep authentication, authorization, rendering, and deployment in one app.

Not recommended for version 1: Django REST API plus separate frontend.

- DRF is already listed in `requirements.txt`, but no API consumers or serializers were found.
- A separate frontend would add authentication, routing, deployment, CORS, API versioning, and E2E complexity before the monolith is stable.

## 6. Architecture Options Comparison

### Option A - Modern Django Monolith

Benefits:

- Closest to current code structure.
- Least migration risk.
- Strong fit for server-rendered music-library workflows.
- Easiest to test with Django TestCase.
- Simple production deployment.

Drawbacks:

- Less flashy than an SPA.
- Requires disciplined template organization to avoid repeating current template problems.

Complexity: Medium  
Maintenance cost: Medium  
Learning value: High for Django recovery, security, testing, deployment  
Portfolio value: High if documented as a recovery and modernization case study  
Deployment complexity: Medium  
Test complexity: Medium  
Migration risk: Medium  
Suitability: Very high  
Relative effort: Large

### Option B - Django plus HTMX/Alpine

Benefits:

- Keeps a single Django deployment.
- Improves interactive actions like favourite toggles, playlist additions, search filtering, and player state.
- Avoids SPA build complexity.

Drawbacks:

- Adds another interaction layer.
- Requires careful progressive enhancement and tests.

Complexity: Medium  
Maintenance cost: Medium  
Learning value: High  
Portfolio value: High  
Deployment complexity: Medium  
Test complexity: Medium to Large  
Migration risk: Medium  
Suitability: High as a staged enhancement  
Relative effort: Large

### Option C - Django REST API plus Separate Frontend

Benefits:

- Clear separation for future mobile/frontend clients.
- Strong API portfolio signal.
- DRF is already pinned in `requirements.txt`.

Drawbacks:

- No current API consumer exists.
- Adds API auth, CORS, deployment split, frontend build tooling, serializer tests, and browser E2E surface.
- Risks obscuring the recovery goal.

Complexity: Very large  
Maintenance cost: High  
Learning value: High, but broad  
Portfolio value: High only if executed fully  
Deployment complexity: High  
Test complexity: Very large  
Migration risk: High  
Suitability: Low for version 1  
Relative effort: Very large

### Option D - Controlled Rebuild Inside Same Django Repository

Benefits:

- Allows selective replacement of brittle views/templates.
- Preserves repository history, domain concepts, migrations where useful, and deployment simplicity.
- Can happen page-by-page after tests.

Drawbacks:

- Requires discipline to avoid rewriting too much at once.
- Data migrations still need careful review.

Complexity: Large  
Maintenance cost: Medium  
Learning value: High  
Portfolio value: High  
Deployment complexity: Medium  
Test complexity: Large  
Migration risk: Medium to High  
Suitability: High after recovery tests  
Relative effort: Large

Primary recommendation: Option A with selective Option B patterns.  
Fallback: Option D if views/templates prove too brittle after recovery.

## 7. Product Scope Options

### Scope 1 - Recovery Portfolio

Intended user: portfolio reviewers and the project owner.

Feature set:

- Existing browsing, search, login, playlists, favourites, recent history.
- Empty and missing-media safety.
- Simple legal demo songs.
- Basic tests and README.

Architecture: recovered Django templates on a supported local runtime.

Complexity: Medium  
Infrastructure: SQLite local, optional simple deployment  
Security needs: local auth, CSRF, authorization, safe settings  
Test burden: Medium  
Deployment burden: Medium  
Relative effort: Medium  
Risks: less impressive product; may leave old architecture visible  
Excluded: model redesign, HTMX, uploads, advanced stats, API, cloud storage

### Scope 2 - Modern Music Library

Intended user: portfolio reviewers, demo users, and the owner as admin.

Feature set:

- Secure local accounts.
- Admin-managed legal song library.
- Responsive library, search, filters, playlists, favourites, recent history.
- Play counts and trending based on a defined play event.
- User profile basics.
- Tests, CI, PostgreSQL deployment, clear docs.

Architecture: modern Django monolith, optional HTMX/Alpine.

Complexity: Large  
Infrastructure: PostgreSQL production, static hosting, approved media storage strategy  
Security needs: production settings, auth, authorization, upload/file validation if admin uploads remain enabled  
Test burden: Large  
Deployment burden: Large  
Relative effort: Large  
Risks: schema and UI scope creep  
Excluded: public uploads, moderation, recommendation engine, mobile app, separate frontend

### Scope 3 - Extended Streaming Platform

Intended user: real public users uploading or discovering media.

Feature set:

- User uploads, moderation, cloud media, signed URLs, background processing, analytics, API, advanced discovery, recommendations.

Architecture: likely Django plus object storage, background workers, cache, API, and possibly a separate frontend.

Complexity: Very large  
Infrastructure: PostgreSQL, object storage, worker queue, Redis, monitoring, backups  
Security needs: high, including upload abuse controls, copyright reporting, moderation, retention, deletion  
Test burden: Very large  
Deployment burden: Very large  
Relative effort: Very large  
Risks: legal, operational, security, cost, scope  
Excluded: none by default, which is the problem

Recommendation: Scope 2.

## 8. Product Decision Register

| Decision | Why it matters | Options | Recommended default | Blocks |
| --- | --- | --- | --- | --- |
| Final project name | Controls branding, URLs, README, UI | Keep GALVANIC, rename, temporary codename | Rename before UI redesign | UI/Docs |
| Portfolio vs real product | Sets security, legal, uptime expectations | Portfolio demo, private app, public product | Portfolio demo | Deployment/Security |
| Public vs private song library | Determines browsing and auth rules | Public browse, login-only, mixed | Public browse for demo songs | Auth/UI |
| User uploads vs admin-managed songs | Uploads add legal and security complexity | Admin-only, user uploads, deferred | Admin-only v1 | Media/Data |
| Anonymous playback | Affects history and play counts | Allow playback, previews only, login required | Allow demo playback but track history only for users | Playback/Auth |
| Login requirement | Determines protected routes | Browse public, all login, hybrid | Hybrid | Auth/UI |
| Google authentication | Current UI exposes it but credentials absent | Keep now, remove/defer, allauth-only | Defer Google until local auth stable | Auth/Deps |
| Playlist privacy | Affects schema and URLs | Private, public, unlisted | Private v1 | Playlist model |
| Favourite behavior | `is_fav` row vs unique like | Toggle row, create/delete, soft state | Unique `(user, song)` like | Data model |
| Recent-history policy | Affects duplicate rows and timestamps | Latest unique songs, every play event, retention limit | Separate `ListeningHistory` for recent unique plus optional `PlayEvent` | Playback/Data |
| Play-count definition | Critical for trending accuracy | Detail view, play button click, audio-start event, completed play | Server POST when user starts playback | Stats |
| Trending definition | Product and query design | All-time plays, recent window, weighted | All-time v1, recent window deferred | Stats/UI |
| Media-storage strategy | Affects deployment and legal policy | Local, platform disk, object storage | Local dev, object storage only if deployment requires persistent media | Deployment |
| Legal demo-media strategy | Avoids copyright risk | Synthetic, public-domain, CC-licensed, owner-created | Small curated authorized set | Demo/Docs |
| API requirement | Determines DRF retention | None, internal AJAX endpoints, public API | No public API v1 | Architecture |
| Separate frontend | Adds cost and deployment split | Django templates, HTMX, SPA | No separate frontend v1 | Architecture |
| Production database | Affects deployment and migrations | SQLite, PostgreSQL, managed DB | PostgreSQL | Deployment |
| Hosting provider | Determines config | Render, Railway, Fly.io, VPS | Render or Railway after comparison | Deployment |
| User profile requirements | Affects model | None, basic, rich profile | Basic `UserProfile` only if needed | Data/UI |
| Account deletion | Privacy and legal | Admin-only, self-service, anonymization | Documented self-service later; admin v1 acceptable for demo | Security |
| Moderation | Needed if uploads exist | None, admin review, reports | None v1 because no public uploads | Media |
| Analytics | Privacy and architecture | None, server logs, app analytics | Minimal server logs | Security/Stats |
| Recommendation system | Can become large | None, simple trending, personalized | Trending only v1 | Product |
| Mobile-app plans | Determines API need | None, future, immediate | None v1 | API |

## 9. Preserve, Refactor, Replace, Remove

### `authentication/`

* **Recommendation:** Preserve concept, refactor implementation, and decide django-allauth boundary.
* **Classification:** Recovery
* **Evidence:** `authentication/forms.py` defines `UserLoginForm` and `RegistrationForm`; `authentication/views.py` defines `login_request`, `signup_request`, and `logout_request`; `authentication/urls.py` maps login/signup/logout.
* **Reasoning:** Local auth is useful, but custom views duplicate behavior already available in Django auth and coexist with allauth.
* **Benefits:** Stable account baseline.
* **Risks:** Broken Google UI, redundant auth logic, no password reset.
* **Dependencies:** Social-auth decision, tests.
* **Relative effort:** Medium
* **Approval required:** Yes for removing allauth or changing auth architecture.
* **Verification method:** Signup/login/logout tests and anonymous/protected route tests.

### `musicapp/models.py`

* **Recommendation:** Preserve for recovery, redesign selected relationship models after tests.
* **Classification:** Required overhaul
* **Evidence:** `Song`, `Playlist`, `Favourite`, and `Recent` exist; `Playlist` combines playlist identity and item row; `Favourite` has no uniqueness; `Recent` has no timestamp.
* **Reasoning:** The current models encode product concepts but lack integrity and analytics support.
* **Benefits:** Clear migration path from existing data.
* **Risks:** Schema changes can break archived DB compatibility.
* **Dependencies:** Recovery tests, migration plan.
* **Relative effort:** Large
* **Approval required:** Yes
* **Verification method:** Migration dry-runs, model tests, data migration tests.

### `musicapp/views.py`

* **Recommendation:** Refactor heavily after recovery fixes.
* **Classification:** Recovery first, required overhaul later
* **Evidence:** Hardcoded `Song.objects.get(id=7)`, `.distinct` without parentheses, debug prints, `list(request.POST.keys())[1]`, repeated recent-history logic, GET routes that mutate history.
* **Reasoning:** Useful workflows exist but implementation is brittle.
* **Benefits:** Safer behavior and easier tests.
* **Risks:** High regression risk without tests.
* **Dependencies:** Startup restoration and baseline tests.
* **Relative effort:** Large
* **Approval required:** No for bug fixes; Yes for behavior changes.
* **Verification method:** View tests and browser smoke tests.

### `musicapp/forms.py`

* **Recommendation:** Replace empty placeholder with explicit forms during recovery.
* **Classification:** Recovery
* **Evidence:** File is effectively empty.
* **Reasoning:** Playlist and favourite mutations should not parse arbitrary POST keys.
* **Benefits:** Validation and clearer tests.
* **Risks:** Minor template updates required.
* **Dependencies:** Existing route repair.
* **Relative effort:** Small to Medium
* **Approval required:** No
* **Verification method:** Form and view tests.

### `musicapp/urls.py`

* **Recommendation:** Preserve route intent, refactor mutation route methods and names.
* **Classification:** Recovery
* **Evidence:** Routes include browsing and playback endpoints; `play/<int:song_id>/`, `play_song/<int:song_id>/`, and `play_recent_song/<int:song_id>/` mutate recent history.
* **Reasoning:** User flows are useful, but state-changing GET routes need redesign.
* **Benefits:** Security and clarity.
* **Risks:** Template links must change to POST forms or HTMX actions.
* **Dependencies:** Playback policy decision.
* **Relative effort:** Medium
* **Approval required:** Yes for playback semantics.
* **Verification method:** Method-restriction and CSRF tests.

### Migrations

* **Recommendation:** Preserve during recovery; add reviewed migrations later.
* **Classification:** Recovery
* **Evidence:** `0001` through `0005` align current `Song.language` model state.
* **Reasoning:** Existing migrations are the only schema history for fresh DB recovery.
* **Benefits:** Protects recoverability.
* **Risks:** Archived DB schema may differ.
* **Dependencies:** Migration discovery.
* **Relative effort:** Small for preservation, Large for redesign.
* **Approval required:** Yes for schema changes.
* **Verification method:** `makemigrations --check --dry-run`, `migrate --plan`, fresh DB migration tests.

### Templates

* **Recommendation:** Repair for empty/missing media, then rewrite page-by-page for modern UI.
* **Classification:** Recovery first, required overhaul later
* **Evidence:** `templates/musicapp/*.html` directly access media URLs; `base.html` uses Bootstrap 4 CDN and inline hover/player CSS; auth templates expose Google buttons.
* **Reasoning:** Structure is reusable, visual and safety layers are not.
* **Benefits:** Safer rendering and better portfolio presentation.
* **Risks:** UI rewrite can conflict with view refactors.
* **Dependencies:** Product name, frontend approach, empty-state policy.
* **Relative effort:** Large
* **Approval required:** Yes for branding/UI direction.
* **Verification method:** Template tests and visual/browser smoke tests.

### Custom CSS

* **Recommendation:** Refactor or replace during UI redesign.
* **Classification:** Optional modernization
* **Evidence:** `static/musicapp/css/musicplayer.css` contains large commented blocks and player-specific styling.
* **Reasoning:** Current CSS is narrow and old; useful player pieces can inform new components.
* **Benefits:** Cleaner responsive system.
* **Risks:** Visual regressions.
* **Dependencies:** Frontend approach.
* **Relative effort:** Medium
* **Approval required:** Yes for design direction.
* **Verification method:** Responsive screenshots and accessibility checks.

### Bundled JavaScript libraries

* **Recommendation:** Remove if unused after verification; do not replace until player requirements are defined.
* **Classification:** Optional modernization
* **Evidence:** `static/musicapp/js/amplitude.min.js` and `wavesurfer.min.js` exist; templates observed use native `<audio>`.
* **Reasoning:** Unused bundled libraries add maintenance and licensing/security surface.
* **Benefits:** Smaller static footprint.
* **Risks:** Hidden usage could break if not searched/tested.
* **Dependencies:** Full static search and player decision.
* **Relative effort:** Small
* **Approval required:** No after verification.
* **Verification method:** Static search, browser playback tests.

### `musicplayer/settings.py`

* **Recommendation:** Preserve for recovery, refactor for production readiness.
* **Classification:** Recovery first, required overhaul later
* **Evidence:** Active settings module; uses `python-decouple`; `DEBUG` defaults true; `ALLOWED_HOSTS` is empty; SQLite default; commented static root.
* **Reasoning:** It is the active configuration but unsafe for deployment.
* **Benefits:** Stable startup then cleaner production posture.
* **Risks:** Settings changes can block imports.
* **Dependencies:** Runtime restoration.
* **Relative effort:** Medium
* **Approval required:** No for safe settings; Yes for settings architecture changes.
* **Verification method:** Django checks and deployment checks.

### `musicplayer/settings1/`

* **Recommendation:** Remove or archive only after verification.
* **Classification:** Optional modernization
* **Evidence:** Default `manage.py` uses `musicplayer.settings`; `settings1/developement.py` and `settings1/production.py` duplicate app settings and use placeholder PostgreSQL config.
* **Reasoning:** Duplicate settings confuse recovery and deployment.
* **Benefits:** Simpler docs and fewer false paths.
* **Risks:** Unknown legacy use.
* **Dependencies:** Confirm no scripts/env use it.
* **Relative effort:** Small
* **Approval required:** Yes
* **Verification method:** Search references, settings import tests.

### django-allauth configuration

* **Recommendation:** Defer Google OAuth and decide whether to keep allauth after local auth recovery.
* **Classification:** Product decision
* **Evidence:** allauth apps/settings are active; `accounts/` is mounted; auth templates call `provider_login_url 'google'`; no credentials are present.
* **Reasoning:** Broken OAuth UI is worse than a deliberately deferred feature.
* **Benefits:** Clear auth story.
* **Risks:** Removing allauth changes dependencies and templates.
* **Dependencies:** Product decision.
* **Relative effort:** Medium
* **Approval required:** Yes
* **Verification method:** Auth flow tests.

### Dependency list

* **Recommendation:** Preserve unchanged for first reproduction, then modernize deliberately.
* **Classification:** Recovery first, required overhaul later
* **Evidence:** `requirements.txt` pins old packages; runtime install fails at allauth on Python 3.14.6.
* **Reasoning:** Need to distinguish old-app reproduction from modernization.
* **Benefits:** Cleaner diagnosis.
* **Risks:** Security exposure if old dependencies are deployed.
* **Dependencies:** Python 3.8 runtime.
* **Relative effort:** Large
* **Approval required:** Yes for broad upgrades.
* **Verification method:** Clean install, `pip check`, tests.

### Admin setup

* **Recommendation:** Preserve and later improve ModelAdmin classes.
* **Classification:** Optional modernization
* **Evidence:** `musicapp/admin.py` registers all four models using wildcard import and no custom admin.
* **Reasoning:** Admin-managed songs are likely v1 media strategy; better admin filters/search will help.
* **Benefits:** Better content management without public uploads.
* **Risks:** Low.
* **Dependencies:** Model decisions.
* **Relative effort:** Small to Medium
* **Approval required:** No
* **Verification method:** Admin smoke tests.

### README and recovery documentation

* **Recommendation:** Preserve and expand.
* **Classification:** Recovery and required overhaul
* **Evidence:** `README.md` documents recovery status and media notice; `SYSTEM_RECOVERY_ANALYSIS.md`, `RUNTIME_VERIFICATION_REPORT.md`, and `PROJECT_RECOVERY_CHECKLIST.md` document current state and phases.
* **Reasoning:** Documentation is a portfolio asset and governance guardrail.
* **Benefits:** Strong project narrative.
* **Risks:** Docs may drift from implementation.
* **Dependencies:** Completed milestones.
* **Relative effort:** Medium
* **Approval required:** No
* **Verification method:** Docs reviewed against commands and code.

## 10. Data-Model Assessment

Current model issues:

- `Song` mixes artist/album text fields and file fields without timestamps, slugs, indexes, validation, or nullable strategy.
- `Playlist` combines playlist header and playlist item in one row.
- `Favourite` allows duplicate user-song rows and stores `is_fav` even though row existence could represent the favourite.
- `Recent` has no timestamp, no ordering field beyond `id`, and does not distinguish history from play event analytics.

Recommended version-1 model map:

### Song

- Purpose: catalog item playable in the library.
- Key fields: title/name, slug, album text or FK, artist text or FK, language/genre, year, cover image, audio file, duration optional, is_active, created_at, updated_at.
- Relationships: optional FK to Artist/Album if approved.
- Constraints: unique slug; title not globally unique.
- Indexes: title, language/genre, artist/singer, created_at.
- Timestamps: yes.
- Deletion: protected or soft-deactivate if referenced by history.
- Privacy: public demo songs.
- Needed v1: yes.
- Migration complexity: Medium.

### Playlist

- Purpose: user-owned collection.
- Key fields: user, name, slug or id, description optional, is_private, created_at, updated_at.
- Relationships: one user to many playlists; many songs through PlaylistItem.
- Constraints: unique `(user, name)` or `(user, slug)`.
- Indexes: user, updated_at.
- Deletion: cascade items.
- Privacy: private v1.
- Needed v1: yes.
- Migration complexity: Large.

### PlaylistItem

- Purpose: song membership and ordering.
- Key fields: playlist, song, position, added_at.
- Relationships: FK playlist, FK song.
- Constraints: unique `(playlist, song)`; optional unique `(playlist, position)`.
- Indexes: playlist, song.
- Deletion: cascade on playlist; cascade or protect on song per product decision.
- Privacy: inherits playlist.
- Needed v1: yes.
- Migration complexity: Large.

### Favourite or Like

- Purpose: user-song preference.
- Key fields: user, song, created_at.
- Relationships: FK user, FK song.
- Constraints: unique `(user, song)`.
- Indexes: user, song, created_at.
- Deletion: cascade on user; cascade or preserve anonymized aggregate on song depending analytics decision.
- Privacy: private.
- Needed v1: yes.
- Migration complexity: Medium.

### ListeningHistory

- Purpose: user-facing recent listening list.
- Key fields: user, song, last_played_at, play_count_for_user optional.
- Relationships: FK user, FK song.
- Constraints: unique `(user, song)` if recent is latest-unique.
- Indexes: `(user, -last_played_at)`.
- Deletion: cascade on user; set null or cascade on song based product decision.
- Privacy: private.
- Needed v1: yes if recent history remains.
- Migration complexity: Medium.

### PlayEvent

- Purpose: analytics event for play counts/trending.
- Key fields: user nullable, song, occurred_at, source/page, session_key optional.
- Relationships: FK song; nullable FK user.
- Constraints: none initially; deduping is application logic.
- Indexes: song, occurred_at, user.
- Deletion: cascade/anonymize on user deletion.
- Privacy: medium; it records behavior.
- Needed v1: optional, needed if trending/play counts must be accurate.
- Migration complexity: Medium.

### SongStatistics

- Purpose: cached aggregates for play counts/trending.
- Key fields: song, total_plays, updated_at.
- Relationships: one-to-one song.
- Constraints: unique song.
- Indexes: total_plays.
- Deletion: cascade on song.
- Privacy: aggregate only.
- Needed v1: optional; can calculate from PlayEvent until scale demands caching.
- Migration complexity: Small.

### UserProfile

- Purpose: display name/avatar/preferences.
- Key fields: user one-to-one, display_name, avatar optional, created_at, updated_at.
- Relationships: one-to-one User.
- Constraints: unique user.
- Indexes: display_name optional.
- Deletion: cascade on user.
- Privacy: profile visibility decision required.
- Needed v1: optional unless profile page is in scope.
- Migration complexity: Small.

Deferred future model map:

- Artist: useful when the catalog grows beyond simple text fields.
- Album: useful for album pages and cover reuse.
- Genre: useful if language is not enough for discovery.
- Upload: only if users upload media.
- MediaAsset: useful if one song has multiple encodings/artwork variants.
- ModerationReport: only if public uploads or user-generated content exists.

Do not design unnecessary models for version 1. Artist/Album/Genre can remain text fields until catalog complexity justifies normalization.

## 11. Authentication Architecture

Current state:

- Custom local auth exists.
- Django auth user model is used directly.
- django-allauth is installed and configured.
- Google OAuth UI appears in login/signup templates.
- Email verification is disabled.
- Password reset is not implemented in custom views.
- Rate limiting is absent.

Recommended authentication path:

1. Recover local authentication first with tests.
2. Temporarily remove or hide Google OAuth UI unless credentials and allauth maintenance are approved.
3. Prefer Django's built-in auth views for login/logout/password reset, or migrate intentionally to django-allauth for all account flows. Avoid maintaining two competing systems long term.
4. Add password reset before public testing if local accounts are used.
5. Add email verification only if public registration is enabled.
6. Add rate limiting before public deployment.
7. Add account deletion/data export decision before production if real users are expected.

* **Recommendation:** Use Django auth plus built-in auth views for version 1, and defer Google OAuth.
* **Classification:** Required overhaul
* **Evidence:** Custom views in `authentication/views.py`; allauth configured in `musicplayer/settings.py`; Google buttons in auth templates; dependency installation fails at old allauth.
* **Reasoning:** Built-in auth reduces custom security surface. Deferred OAuth avoids broken UI and dependency pressure during recovery.
* **Benefits:** Simpler tests, fewer moving parts, clearer security posture.
* **Risks:** Removing allauth later touches settings, URLs, templates, and dependencies.
* **Dependencies:** Product approval on Google login.
* **Relative effort:** Medium
* **Approval required:** Yes
* **Verification method:** Auth test suite, password reset tests, security checklist.

## 12. Media Strategy

Version-1 recommendation:

- Local development: tiny generated or authorized fixture audio, placeholder cover art, and user-owned local files outside Git.
- Portfolio deployment: small curated legal demo library only, with explicit attribution if required.
- Storage: local filesystem for development; choose persistent platform storage or object storage for production based on host.
- Git policy: never commit commercial audio or private archived media; keep `media/.gitkeep`; commit only tiny synthetic fixtures under test directories if needed.
- Uploads: admin-managed only for version 1.
- Upload limits: define max audio and cover image size before public testing.
- Validation: extension, MIME type, size, and safe filename validation.
- Cover art: required fallback image; never assume `song_img.url` exists.
- Cleanup: remove orphan files when replacing/deleting admin media if storage supports it.
- Missing media: render unavailable state and disable playback button.
- Deployment implications: persistent media storage is required if admin uploads happen in production.
- Legal considerations: store attribution and license information for demo media.

* **Recommendation:** Admin-managed legal demo media only for version 1.
* **Classification:** Required overhaul
* **Evidence:** Original media is intentionally removed; `media/.gitkeep` exists; templates assume file URLs; README includes media notice.
* **Reasoning:** User uploads would require moderation, abuse handling, and copyright policy that exceed version 1 needs.
* **Benefits:** Safe portfolio demo and simpler deployment.
* **Risks:** Small demo library may feel limited.
* **Dependencies:** Legal demo-media decision and storage decision.
* **Relative effort:** Medium
* **Approval required:** Yes
* **Verification method:** Media fixture tests, missing-media tests, deployment media smoke test.

## 13. Frontend Overhaul Strategy

Current frontend:

- Bootstrap 4 via CDN in `base.html`.
- Font Awesome 4 via CDN.
- Google Fonts via HTTP/HTTPS.
- Inline CSS in templates.
- Custom CSS in `static/musicapp/css/musicplayer.css`.
- Native audio controls.
- Direct image/audio URL access.
- Fixed player footer and fixed widths such as `width: 1230px`.
- Page-specific repeated song-card markup.

Recommended frontend approach:

- Keep Django templates.
- Upgrade to Bootstrap 5 or build a small custom CSS layer; choose one after branding decision.
- Use HTMX only for focused interactions: favourite toggle, add/remove playlist item, search/filter update, and play-event tracking.
- Use native audio controls for v1 unless a custom player is specifically required.
- Remove unused Amplitude/WaveSurfer only after confirming no usage.
- Build reusable partials: song card, song table row, player bar, empty state, form errors, pagination.
- Add explicit empty/error states for every list and media component.

Page-by-page redesign plan:

- Base layout: responsive navigation, auth menu, accessible focus states, no inherited `GALVANIC` unless approved.
- Homepage: sections for recent, trending, recently added, language/category highlights; safe empty state.
- Music library: searchable/filterable list with pagination and cover fallbacks.
- Search results: distinct page state for query, filters, no results, invalid filters.
- Song detail: safe media card, metadata, favourite/playlist actions, play button.
- Player: bottom or inline player with disabled state when audio missing.
- Recent history: user-owned list, clear-history decision, empty state.
- Favourites: card/list view with POST remove action.
- Playlists: playlist index, playlist detail, create/edit/delete flows after model decision.
- Login/signup: remove broken Google buttons if OAuth deferred; clear errors and password reset links.
- User profile: basic account summary and history/privacy links if approved.
- Error pages: 404, 403, 500 templates with safe branding.
- Empty states: shared component for no songs, no media, no playlists, no favourites, no history, no search results.

## 14. Dependency Modernization Strategy

Dependency classifications:

| Dependency | Classification | Recommendation |
| --- | --- | --- |
| Django==3.0.8 | Required now, obsolete/security-sensitive | Reproduce on Python 3.8, then upgrade after tests |
| asgiref, pytz, sqlparse | Django transitive/support | Let modern Django constrain versions later |
| django-allauth==0.42.0 | Optional/product-dependent, current blocker | Keep only if social auth approved; otherwise remove after tests |
| django-crispy-forms==1.9.1 | Required by auth templates | Upgrade or replace with manual forms/Bootstrap 5-compatible package |
| django-debug-toolbar==2.2 | Development-only | Keep only in dev requirements if used |
| django-environ==0.4.5 | Likely unused with active settings | Remove if `settings1/` removed and no usage remains |
| django-model-utils==4.0.0 | Unused in inspected code | Remove after verification |
| django-redis==4.12.1 | Unused/production-only if caching approved | Remove or defer |
| djangorestframework==3.11.0 | Unfinished/API-only | Remove unless API approved |
| python-decouple==3.3 | Required now | Upgrade or standardize env parsing |
| argon2-cffi, cffi, pycparser | Password hashing/native stack | Keep only if argon2 hasher configured; otherwise remove if unused |
| requests, requests-oauthlib, oauthlib, python3-openid, defusedxml, idna, chardet, certifi, urllib3, six | allauth/social dependency stack | Keep only if allauth/social auth retained |
| python-slugify, text-unidecode | Optional for future slugs | Use if slug fields added; otherwise remove |

Modernization sequence:

1. Reproduce old app using Python 3.8 and unchanged requirements.
2. If unchanged install still fails, make the smallest dependency pin repair and document it.
3. Restore Django startup and tests.
4. Split development-only and production dependencies only after tests.
5. Remove verified unused dependencies one at a time.
6. Upgrade Django through a reviewed path, preferably to a current LTS target.
7. Add production dependencies such as `gunicorn` and database driver only when deployment branch begins.

Recommended supported target:

- Python: 3.12 for the modernized target, after recovery on 3.8.
- Django: current supported LTS if available in the project window; otherwise latest stable supported Django after release-note review.
- Database driver: `psycopg` or `psycopg2-binary` based on hosting compatibility.
- Authentication package: Django auth built-in views; django-allauth only if OAuth is approved.
- Test framework: start with Django TestCase; consider pytest-django after baseline suite if team prefers.
- Formatting/linting: Ruff and Black.
- Production server: Gunicorn on hosted Linux platform.

## 15. Testing Strategy

Test framework recommendation:

- Start with Django `TestCase` and `Client` because the project is small and currently has no test suite.
- Add factories or small helper functions before adding factory_boy.
- Consider pytest-django later if test ergonomics become a bottleneck.

Test structure:

- `authentication/tests/test_auth_views.py`
- `musicapp/tests/test_models.py`
- `musicapp/tests/test_browsing_views.py`
- `musicapp/tests/test_playlists.py`
- `musicapp/tests/test_favourites.py`
- `musicapp/tests/test_history.py`
- `musicapp/tests/test_media_safety.py`
- `musicapp/tests/test_authorization.py`

Minimum test suite before model redesign:

- Settings import.
- URL reverse coverage.
- Empty homepage/all-songs/language/recent/favourite/playlist pages.
- Song detail valid and missing ID.
- Missing image/audio fields.
- Login/signup/logout.
- Anonymous mutation rejection.
- Favourite and playlist ownership.
- Playback/history method policy.

Minimum test suite before Django upgrade:

- Full recovery suite.
- Migration drift check.
- Auth flows.
- Media file handling.
- Template rendering for core pages.

Minimum test suite before UI rewrite:

- View behavior tests for every page.
- Snapshot-light assertions for key text/states.
- Browser smoke tests for mobile and desktop if possible.

Minimum test suite before deployment:

- `python manage.py check --deploy` where appropriate.
- Static collection smoke test.
- Migration plan/apply in disposable database.
- Production settings import.
- Deployment smoke tests for homepage, login, library, admin, media.

Coverage target:

- Do not chase a number early; require all critical workflows and security-sensitive mutations.
- After baseline, target 80% meaningful coverage.

CI commands:

```powershell
python -m pip check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## 16. Security Architecture

Required before local recovery:

- Keep secrets in `.env`; never commit `.env`.
- Restore dependency installation in a local virtual environment.
- Confirm active settings module.
- Confirm CSRF middleware remains enabled.
- Avoid migrations until planned.

Required before public testing:

- `DEBUG=False` path works.
- `ALLOWED_HOSTS` configured.
- Login required for user-owned pages and mutations.
- POST-only mutation endpoints.
- CSRF-protected forms.
- Cross-user authorization tests.
- Missing media and empty DB safe rendering.
- Remove broken OAuth buttons or configure them.
- Password reset if public local accounts are allowed.
- Basic rate limiting for login/signup.

Required before production:

- Secure cookies, HTTPS redirect, HSTS, CSRF trusted origins.
- Production database credentials from environment.
- Dependency scan.
- Admin protection and strong admin creation docs.
- File upload validation and size limits.
- Logging without secrets.
- Error pages without stack traces.
- Privacy policy for play history/profile data if real users exist.
- Account deletion/data retention decision.
- Backups and rollback.

## 17. Deployment Architecture

### Render

Benefits: Django-friendly, managed PostgreSQL, GitHub deploys, simple env vars, predictable web service model.  
Drawbacks: free-tier sleep/cost considerations, persistent media requires object storage or paid disk options.  
Complexity: Medium.  
Suitability: High for version 1.

### Railway

Benefits: Fast setup, managed PostgreSQL, simple GitHub deployments.  
Drawbacks: cost predictability can vary; media persistence still needs planning.  
Complexity: Medium.  
Suitability: High.

### Fly.io

Benefits: strong control, global deployment, persistent volumes possible.  
Drawbacks: more operational complexity; Docker likely becomes useful.  
Complexity: Large.  
Suitability: Medium.

### VPS

Benefits: maximum control and stable cost if managed well.  
Drawbacks: server administration, backups, security updates, deploy automation, TLS, monitoring.  
Complexity: Very large.  
Suitability: Low for version 1 unless learning ops is a goal.

### PythonAnywhere or similar Django host

Benefits: simple Django hosting and admin-managed demos.  
Drawbacks: less modern deployment story; limitations on storage/background jobs.  
Complexity: Small to Medium.  
Suitability: Medium for simple portfolio.

Recommended version-1 deployment:

- Render or Railway web service.
- Managed PostgreSQL.
- Gunicorn.
- Static files via WhiteNoise or platform-supported static serving.
- Media via small persistent storage or object storage only if needed.
- GitHub deployment with environment variables.
- Backups enabled for production database.

Do not create deployment files until recovery tests pass.

## 18. Migration and Rollback Strategy

Strategy:

- Tag baseline recovery after dependency startup and empty-state tests pass.
- Use one focused branch per behavior or schema change.
- Never combine dependency upgrades, model redesign, and UI rewrite in one pull request.
- Run `makemigrations --check --dry-run` before schema work.
- Review generated migrations manually.
- Test migrations on a fresh disposable database.
- Test data migrations with synthetic fixtures before archived DB compatibility work.
- Treat archived DB import as a separate reviewed plan.
- Use rollback checkpoints before Django upgrade, playlist normalization, favourite constraint changes, and production deployment.
- Use feature flags or settings switches only where partial rollout is useful, such as new player-history semantics.
- Tag important milestones: `recovery-startup`, `recovery-empty-safe`, `recovery-tested`, `schema-v1`, `ui-v1`, `v1.0.0`.

Never combine in one PR:

- Django version upgrade and schema migration.
- Playlist model normalization and UI redesign.
- Auth architecture change and dependency cleanup.
- Media storage change and deployment provider change.
- Test infrastructure migration and feature behavior change.
- Large template rewrite and view behavior refactor.

## 19. Work Breakdown Structure

### Phase 1 - Runtime Restoration

Task: install Python 3.8 and recreate `.venv`.  
Dependencies: none.  
Acceptance: `py -0p` lists Python 3.8; `.venv` uses Python 3.8.  
Tests: version and pip commands.  
Effort: Small.  
Risk: Medium.

Task: retry unchanged requirements on Python 3.8.  
Dependencies: Python 3.8.  
Acceptance: install succeeds or first blocker documented.  
Tests: `pip check`.  
Effort: Small.  
Risk: Medium.

Task: make minimal dependency repair if unchanged install fails.  
Dependencies: documented blocker.  
Acceptance: dependencies install reproducibly.  
Tests: `pip check`.  
Effort: Medium.  
Risk: Medium.

Task: run Django startup diagnostics.  
Dependencies: dependencies installed.  
Acceptance: `manage.py check`, `showmigrations`, `migrate --plan`, `test` produce documented results.  
Tests: required commands.  
Effort: Small.  
Risk: Medium.

### Phase 2 - Safe Local Database

Task: review migrations and create disposable local DB.  
Dependencies: startup diagnostics.  
Acceptance: migrations apply to ignored local SQLite DB.  
Tests: `showmigrations`, admin smoke.  
Effort: Medium.  
Risk: Medium.

### Phase 3 - Empty Library and Media Safety

Task: remove hardcoded fallback song IDs and allow `last_played=None`.  
Dependencies: startup.  
Acceptance: no `Song.objects.get(id=7)` remains.  
Tests: empty homepage/all-songs/language/recent tests.  
Effort: Medium.  
Risk: High.

Task: guard template media URLs and add cover/audio unavailable states.  
Dependencies: last_played safety.  
Acceptance: pages render with missing files.  
Tests: missing image/audio tests.  
Effort: Medium.  
Risk: Medium.

### Phase 4 - Core Behavior Recovery

Task: fix search and browsing behavior.  
Dependencies: empty safety.  
Acceptance: query/filter behavior defined.  
Tests: search/filter tests.  
Effort: Medium.  
Risk: Medium.

Task: repair local auth flows.  
Dependencies: startup.  
Acceptance: signup/login/logout pass tests.  
Tests: auth tests.  
Effort: Medium.  
Risk: Medium.

Task: decide and clean up Google OAuth UI.  
Dependencies: auth tests.  
Acceptance: no broken OAuth UI remains, or OAuth is configured.  
Tests: auth template and route tests.  
Effort: Medium.  
Risk: Medium.

Task: repair favourite mutations.  
Dependencies: auth recovery.  
Acceptance: POST-only, login-required, duplicate-safe.  
Tests: favourite tests.  
Effort: Medium.  
Risk: Medium.

Task: repair playlist mutations with current model.  
Dependencies: auth recovery.  
Acceptance: `.distinct()` fixed, explicit POST fields, ownership enforced.  
Tests: playlist tests.  
Effort: Medium.  
Risk: Medium.

Task: repair playback/recent-history flow.  
Dependencies: playback product decisions.  
Acceptance: no GET history mutation; recent policy tested.  
Tests: playback/history tests.  
Effort: Medium.  
Risk: High.

### Phase 5 - Baseline Test Suite

Task: organize test modules and helpers.  
Dependencies: startup.  
Acceptance: meaningful test layout exists.  
Tests: full test suite.  
Effort: Medium.  
Risk: Low.

Task: cover recovered core workflows.  
Dependencies: phases 3-4.  
Acceptance: tests cover public pages, auth, user features, history, media.  
Tests: full test suite.  
Effort: Large.  
Risk: Medium.

### Phase 6 - Schema Modernization

Task: normalize Playlist and PlaylistItem with reviewed migration.  
Dependencies: baseline tests, approval.  
Acceptance: old behavior preserved or migration documented.  
Tests: model/view/migration tests.  
Effort: Large.  
Risk: High.

Task: add Favourite uniqueness.  
Dependencies: duplicate policy approval.  
Acceptance: unique user-song favourite.  
Tests: duplicate tests and migration tests.  
Effort: Medium.  
Risk: Medium.

Task: add timestamps/history model changes.  
Dependencies: recent/play-count decisions.  
Acceptance: timestamps and ordering stable.  
Tests: history tests.  
Effort: Medium.  
Risk: Medium.

### Phase 7 - Dependency and Django Modernization

Task: remove unused dependencies one at a time.  
Dependencies: tests.  
Acceptance: clean install and tests after each removal.  
Tests: `pip check`, full suite.  
Effort: Medium.  
Risk: Medium.

Task: upgrade Python target.  
Dependencies: tests.  
Acceptance: supported Python documented and tests pass.  
Tests: full suite.  
Effort: Medium.  
Risk: Medium.

Task: upgrade Django through reviewed steps.  
Dependencies: Python target and tests.  
Acceptance: supported Django target reached.  
Tests: full suite, warnings reviewed.  
Effort: Large.  
Risk: High.

### Phase 8 - UI and Branding

Task: choose name and design direction.  
Dependencies: owner decision.  
Acceptance: branding decision documented.  
Tests: none.  
Effort: Small.  
Risk: Medium.

Task: rebuild base layout.  
Dependencies: branding decision.  
Acceptance: responsive nav and layout.  
Tests: template/browser smoke.  
Effort: Medium.  
Risk: Medium.

Task: rebuild library/detail/player pages.  
Dependencies: base layout and recovered view tests.  
Acceptance: responsive, accessible, empty-safe.  
Tests: browser smoke and view tests.  
Effort: Large.  
Risk: Medium.

Task: rebuild account/user pages.  
Dependencies: auth architecture.  
Acceptance: clear account flows.  
Tests: auth/browser tests.  
Effort: Medium.  
Risk: Medium.

### Phase 9 - Deployment and Release

Task: add CI.  
Dependencies: test suite.  
Acceptance: GitHub checks run install, checks, migrations, tests.  
Tests: CI pass.  
Effort: Medium.  
Risk: Medium.

Task: add production settings and deployment config.  
Dependencies: security baseline.  
Acceptance: deployable with env vars.  
Tests: deploy smoke.  
Effort: Large.  
Risk: High.

Task: update README and portfolio docs.  
Dependencies: deployed app.  
Acceptance: setup, tests, deployment, screenshots, recovery story.  
Tests: docs review.  
Effort: Medium.  
Risk: Low.

## 20. Parallelization Plan

Can run in parallel after startup restoration:

- Auth flow tests and public page empty-state tests.
- Documentation updates and dependency usage audit.
- Media legal strategy and frontend branding decisions.
- Admin usability planning and README expansion.
- Deployment host comparison and CI design.

Must remain sequential:

- Python/runtime restoration before Django diagnostics.
- Dependency installation before migration discovery.
- Empty-library safety before broad UI rewrite.
- Baseline tests before model redesign.
- Model redesign before playlist UI overhaul.
- Auth architecture decision before OAuth dependency cleanup.
- Production settings before deployment.

Must not overlap:

- Multiple branches editing `musicapp/views.py` broadly.
- Playlist schema redesign and playlist template rewrite.
- Auth package removal and auth template redesign.
- Django upgrade and dependency cleanup.
- Settings consolidation and deployment config.
- CSS system rewrite and base template redesign by separate workers without coordination.

## 21. Risk Register

| Risk | Category | Likelihood | Severity | Affected phases | Evidence | Mitigation | Contingency | Verification | Owner decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Old dependencies do not install | Runtime | High | High | 1 | Runtime report allauth failure | Use Python 3.8 first, smallest pin change | Document and upgrade targeted package | Clean install | No |
| Unsupported Python | Runtime | High | High | 1 | `py -0p` none; Python 3.14.6 only | Install Python 3.8 for recovery | Move directly to modernization only with approval | Version commands | No |
| Incomplete tests | Quality | High | High | All | Empty tests files | Build baseline suite before overhaul | Freeze schema/UI changes | CI/test pass | No |
| Archived DB incompatible | Data | Medium | High | Schema | Unknown private DB | Treat import as separate plan | Use fresh DB only | Migration/import rehearsal | Yes |
| Missing media crashes pages | Runtime | High | High | Recovery/UI | Direct `.url` template access | Guard file fields | Disable playback when missing | Media tests | No |
| Copyrighted media reintroduced | Legal | Medium | Critical | Media/Deploy | Original media removed by design | Legal media policy | Remove media and rotate demo | Repo audit | Yes |
| Auth overlap | Security | High | High | Auth/Deps | Custom auth plus allauth | Decide one architecture | Hide OAuth | Auth tests | Yes |
| Schema redesign breaks data | Data | Medium | High | Schema | Playlist model denormalized | Reviewed migrations | Roll back to tag | Migration tests | Yes |
| GET mutations remain | Security | High | High | Recovery | Playback routes mutate history | POST-only endpoints | Disable history tracking | Method tests | Yes for policy |
| Frontend scope creep | Product | Medium | Medium | UI | Many pages need rewrite | Page-by-page branches | Defer advanced player | Visual QA | Yes |
| Unnecessary SPA conversion | Architecture | Medium | High | Architecture | No API consumer found | Keep monolith v1 | Re-evaluate later | Architecture review | Yes |
| Deployment cost surprises | Ops | Medium | Medium | Deploy | Provider undecided | Compare free/paid limits | Choose simpler host | Deployment review | Yes |
| Cloud-storage complexity | Ops | Medium | Medium | Media/Deploy | Media persistence needed | Admin-only small media | Local demo only | Deploy smoke | Yes |
| Weak authorization | Security | High | High | Recovery | User-specific views use request.user | Login decorators and ownership filters | Temporarily disable feature | Authz tests | No |
| Data loss | Data | Low | Critical | DB | Archived DB private | Never touch archive | Restore from archive copy only in reviewed plan | Git/database audit | Yes |
| Large Codex changes | Process | Medium | High | All | Broad overhaul request | Focused branches | Split PR | Diff review | No |
| Merge conflicts | Process | Medium | Medium | Views/UI | Centralized view/template files | Parallelization rules | Rebase small branches | Git diff | No |

## 22. Definitions of Done

Recovery milestone:

- Behavior: app installs, starts, migrates fresh DB, renders core pages with empty library and missing media.
- Tests: startup, migrations, public pages, auth, favourites, playlists, recent/history basics.
- Documentation: runtime setup and known limitations.
- Security: no GET mutations for user data, basic auth protection.
- Git state: focused commits merged; recovery tag created.
- Deployment verification: local only is acceptable.

Architecture milestone:

- Behavior: target scope, architecture, auth, media, data model, and deployment decisions approved.
- Tests: baseline suite exists before implementation.
- Documentation: architecture decision records or plan sections updated.
- Security: security requirements mapped by phase.
- Git state: planning docs committed.
- Deployment verification: not required.

Backend milestone:

- Behavior: normalized models where approved, recovered workflows stable, search/history/stats defined.
- Tests: model, view, form, authz, migration tests pass.
- Documentation: data model and API/non-API decision documented.
- Security: ownership and mutation tests pass.
- Git state: schema tags/checkpoints created.
- Deployment verification: staging smoke if available.

Frontend milestone:

- Behavior: responsive original UI for all core pages.
- Tests: view tests pass, browser smoke tests pass.
- Documentation: screenshots and design notes.
- Security: forms retain CSRF and safe auth behavior.
- Git state: page-level branches merged.
- Deployment verification: deployed static assets load.

Security milestone:

- Behavior: production settings secure, auth and uploads hardened, error handling safe.
- Tests: authorization, method, CSRF, upload validation, deploy checks.
- Documentation: security checklist and env docs.
- Git state: security branch merged.
- Deployment verification: `DEBUG=False`, HTTPS, cookies, headers, logs checked.

Deployment milestone:

- Behavior: app deploys from GitHub with database, static files, media strategy, migrations, and health checks.
- Tests: CI passes and production smoke tests pass.
- Documentation: deployment and rollback docs.
- Security: secrets in environment only, backups configured.
- Git state: deployment config merged and tagged.
- Deployment verification: live URL verified.

Version 1.0 release:

- Behavior: approved version-1 product scope complete.
- Tests: full CI pass, deployment smoke pass.
- Documentation: README, architecture, setup, testing, deployment, media policy, recovery story.
- Security: no unaddressed critical security issues.
- Git state: clean release tag `v1.0.0`.
- Deployment verification: live demo works and rollback plan exists.

## 23. Recommended Immediate Actions

1. Fix or intentionally remove the stray first line in `.gitignore` after confirming it is accidental.
2. Commit the recovery documentation files already present after review.
3. Install Python 3.8.x and recreate `.venv`.
4. Retry `requirements.txt` unchanged on Python 3.8.
5. If install fails, make the smallest dependency pin repair and document it.
6. Run Django startup diagnostics.
7. Run migration discovery without applying migrations.
8. Create a disposable local database only after migration plan review.
9. Remove hardcoded fallback song IDs and add empty-library tests.
10. Add baseline tests before any architecture overhaul.

## 24. Final Feasibility Assessment

The overhaul is feasible and worthwhile. The inherited project is not production-ready, but it has a recognizable Django structure, useful domain concepts, and enough existing behavior to recover into a strong portfolio application. The safest path is not to rebuild from scratch. It is to recover runtime first, establish tests, then modernize the backend, schema, UI, security, and deployment in focused branches.

Recommended version-1 target:

- Scope: Modern Music Library.
- Architecture: modern Django monolith with optional HTMX-enhanced interactions.
- Runtime target: recover on Python 3.8, modernize to a supported Python such as 3.12 after tests.
- Django target: recover Django 3.0 behavior first, then upgrade to a supported Django release after tests.
- Database: SQLite for disposable recovery, PostgreSQL for production.
- Media: admin-managed legal demo media only.
- Deployment: Render or Railway with managed PostgreSQL, static-file handling, and a documented media strategy.

The highest-leverage first repair remains environment restoration. Until Django imports successfully, all application-level recommendations are architecture plans based on static evidence rather than runtime-confirmed behavior.
