# Django Music Player — Recovery and Development Checklist

## Progress legend

* [ ] Not started
* [~] In progress
* [x] Complete
* [!] Blocked
* [-] Skipped or intentionally deferred

---

# Phase 0 — Repository Preservation and Governance

## Goal

Preserve the original project safely and establish a clean, secure recovery repository.

## Checklist

* [x] Obtain written permission from both original contributors.
* [x] Store contributor permissions outside the Git repository.
* [x] Download the original project ZIP.
* [x] Preserve an untouched original project copy.
* [x] Create a separate recovery working folder.
* [x] Confirm the ZIP contains no inherited `.git` history.
* [x] Archive the original SQLite database privately.
* [x] Archive the original media files privately.
* [x] Remove the original database from the active repository.
* [x] Remove copyrighted music files from the active repository.
* [x] Add `media/.gitkeep`.
* [x] Remove old website screenshots from the active repository.
* [x] Remove old profile links, repository links, and dead deployment links.
* [x] Replace the old README with a recovery README.
* [x] Preserve the complete MIT License.
* [x] Add Shivay Dwivedi’s recovery and modification copyright notice.
* [x] Remove the hardcoded Django `SECRET_KEY`.
* [x] Configure `SECRET_KEY` using environment variables.
* [x] Configure `DEBUG` using environment variables.
* [x] Add `.env` to `.gitignore`.
* [x] Add and track `.env.example`.
* [x] Ignore `db.sqlite3`.
* [x] Ignore runtime media while keeping `media/.gitkeep`.
* [x] Initialize fresh Git history.
* [x] Create the secure recovery baseline commit.
* [x] Create `backup/clean-recovery-baseline`.
* [x] Create the new GitHub repository.
* [x] Push `main`.
* [x] Push the backup branch.
* [x] Create `recovery/runtime-verification`.
* [x] Push the runtime-verification branch.
* [x] Generate `SYSTEM_RECOVERY_ANALYSIS.md`.
* [ ] Commit and push `SYSTEM_RECOVERY_ANALYSIS.md`.
* [x] Confirm the working tree is clean.

## Exit criteria

* [x] No secrets are committed.
* [x] No personal database is committed.
* [x] No commercial music files are committed.
* [x] Licensing is preserved.
* [x] Original materials are privately archived.
* [x] Fresh Git history exists.
* [x] Recovery work is isolated from `main`.

## Status

**Nearly complete**

---

# Phase 1 — Runtime Environment Verification

## Goal

Determine whether the inherited project can install and start without changing application behavior.

## Checklist

### Repository verification

* [ ] Confirm the active branch is `recovery/runtime-verification`.
* [ ] Confirm the working tree is clean.
* [ ] Read `SYSTEM_RECOVERY_ANALYSIS.md`.
* [ ] Inspect `requirements.txt`.
* [ ] Confirm `.env` exists locally.
* [ ] Confirm `.env` is ignored.
* [ ] Confirm `.env.example` is tracked.

### Python environment

* [ ] Run `py -0p`.
* [ ] Record all installed Python versions.
* [ ] Select the best compatible Python version.
* [ ] Document why that version was chosen.
* [ ] Create `.venv`.
* [ ] Activate `.venv`.
* [ ] Confirm the active Python executable points to `.venv`.
* [ ] Record the Python version.
* [ ] Record the pip version.

### Dependency installation

* [ ] Upgrade only `pip`, `setuptools`, and `wheel`.
* [ ] Attempt to install `requirements.txt` unchanged.
* [ ] Record all installation warnings.
* [ ] Record all failed packages.
* [ ] Identify Python compatibility failures.
* [ ] Identify native Windows build failures.
* [ ] Run `python -m pip check`.

### Django diagnostics

* [ ] Run `python manage.py check`.
* [ ] Run `python manage.py showmigrations`.
* [ ] Run `python manage.py migrate --plan`.
* [ ] Run `python manage.py test`.
* [ ] Do not run migrations.
* [ ] Do not create seed data.
* [ ] Do not modify source code.

### Documentation

* [ ] Create `RUNTIME_VERIFICATION_REPORT.md`.
* [ ] Separate environment failures from code failures.
* [ ] Identify the first confirmed startup blocker.
* [ ] Identify page-level risks not yet tested.
* [ ] Confirm no existing project files were modified.
* [ ] Review the report with ChatGPT.
* [ ] Commit the approved report.
* [ ] Push the report branch.

## Exit criteria

* [ ] Supported recovery Python version is known.
* [ ] Dependency installation result is documented.
* [ ] Django startup state is known.
* [ ] Migration discovery works or its blocker is known.
* [ ] Existing test state is documented.
* [ ] First confirmed repair task is identified.

## Branch

`recovery/runtime-verification`

## Status

**Not started**

---

# Phase 2 — Dependency and Startup Restoration

## Goal

Make the project install successfully and pass Django startup checks.

## Checklist

### Dependency repair

* [ ] Identify the exact dependency causing installation failure.
* [ ] Verify whether the package is actually used.
* [ ] Determine the smallest compatible version change.
* [ ] Avoid broad dependency upgrades.
* [ ] Document every dependency change.
* [ ] Reinstall dependencies in a fresh `.venv`.
* [ ] Run `python -m pip check`.

### Django startup repair

* [ ] Fix confirmed import errors.
* [ ] Fix confirmed settings errors.
* [ ] Confirm `SECRET_KEY` loads from `.env`.
* [ ] Confirm `DEBUG` loads correctly.
* [ ] Confirm the active settings module is `musicplayer.settings`.
* [ ] Verify all installed apps load.
* [ ] Verify django-allauth imports successfully.
* [ ] Verify project URL configuration loads.
* [ ] Verify static and media settings load.
* [ ] Run `python manage.py check`.
* [ ] Run `python manage.py showmigrations`.
* [ ] Run `python manage.py migrate --plan`.
* [ ] Run `python manage.py test`.

### Documentation

* [ ] Document the supported Python version.
* [ ] Document the dependency installation command.
* [ ] Update local setup instructions.
* [ ] Record accepted warnings.
* [ ] Create a focused dependency/startup commit.
* [ ] Review the diff.
* [ ] Push the branch.
* [ ] Open and merge a reviewed pull request.

## Exit criteria

* [ ] A clean environment installs successfully.
* [ ] `python manage.py check` passes.
* [ ] Migrations are discoverable.
* [ ] Settings load from environment variables.
* [ ] No feature behavior has been changed unnecessarily.

## Suggested branches

* `fix/dependency-installation`
* `fix/django-startup`

## Status

**Not started**

---

# Phase 3 — Disposable Local Database Setup

## Goal

Create a safe, fresh local database without touching the archived original database.

## Checklist

* [ ] Confirm `db.sqlite3` is ignored.
* [ ] Confirm the archived database remains outside the repository.
* [ ] Review all existing migration files.
* [ ] Run `python manage.py makemigrations --check --dry-run`.
* [ ] Run `python manage.py migrate --plan`.
* [ ] Review the migration plan.
* [ ] Confirm no unexpected schema changes appear.
* [ ] Run `python manage.py migrate`.
* [ ] Run `python manage.py showmigrations`.
* [ ] Confirm all migrations are applied.
* [ ] Run `python manage.py check`.
* [ ] Create a local development superuser.
* [ ] Start the development server.
* [ ] Verify `/admin/` loads.
* [ ] Verify admin login works.
* [ ] Confirm database tables are empty except system data.
* [ ] Document how to reset the disposable database.
* [ ] Confirm `db.sqlite3` remains untracked.

## Exit criteria

* [ ] Fresh database can be created from migrations.
* [ ] All migrations apply successfully.
* [ ] Admin works.
* [ ] Database remains local and ignored.
* [ ] Archived database remains untouched.

## Suggested branch

`recovery/local-database`

## Status

**Not started**

---

# Phase 4 — Empty Library and Missing Media Safety

## Goal

Make every relevant page render safely when the database contains no songs or media.

## Checklist

### Remove hardcoded assumptions

* [ ] Find every `Song.objects.get(id=7)` occurrence.
* [ ] Remove all hardcoded song-ID fallbacks.
* [ ] Replace them with safe optional queries.
* [ ] Ensure `last_played` may be `None`.
* [ ] Handle missing song lookups safely.
* [ ] Use `get_object_or_404` where appropriate.

### Safe media handling

* [ ] Find every direct `.song_img.url` access.
* [ ] Find every direct `.song_file.url` access.
* [ ] Guard empty file fields.
* [ ] Guard missing physical files.
* [ ] Add a default cover image strategy.
* [ ] Add unavailable-audio messaging.
* [ ] Ensure pages do not crash when `media/` is empty.

### Empty states

* [ ] Add homepage empty state.
* [ ] Add all-songs empty state.
* [ ] Add Hindi-songs empty state.
* [ ] Add English-songs empty state.
* [ ] Add recent-history empty state.
* [ ] Add favourites empty state.
* [ ] Add playlists empty state.
* [ ] Add no-search-results state.
* [ ] Add nonexistent-song handling.

### Tests

* [ ] Test homepage with zero songs.
* [ ] Test all-songs page with zero songs.
* [ ] Test language pages with zero songs.
* [ ] Test recent page with no history.
* [ ] Test favourite page with no favourites.
* [ ] Test playlist page with no playlists.
* [ ] Test nonexistent song ID.
* [ ] Test song without image.
* [ ] Test song without audio.
* [ ] Test missing physical media file.

### Review

* [ ] Run Django checks.
* [ ] Run targeted tests.
* [ ] Run full tests.
* [ ] Review the Git diff.
* [ ] Confirm no unrelated features changed.
* [ ] Commit and push.
* [ ] Review and merge the pull request.

## Exit criteria

* [ ] Public pages render on an empty database.
* [ ] No hardcoded song IDs remain.
* [ ] Missing media is handled gracefully.
* [ ] Tests prove empty-library behavior.

## Branch

`fix/empty-library-safety`

## Status

**Not started**

---

# Phase 5 — Core Browsing and Search Recovery

## Goal

Restore song browsing, filtering, search, and detail pages.

## Checklist

### Song browsing

* [ ] Verify all-songs page behavior.
* [ ] Verify song ordering.
* [ ] Verify song cards render.
* [ ] Verify cover fallback behavior.
* [ ] Verify audio availability indicators.

### Language filters

* [ ] Verify Hindi filter.
* [ ] Verify English filter.
* [ ] Confirm language choices match model values.
* [ ] Add empty results behavior.
* [ ] Add tests for each filter.

### Search

* [ ] Identify searchable fields.
* [ ] Define case-sensitivity behavior.
* [ ] Handle empty search query.
* [ ] Handle no matches.
* [ ] Verify special-character input.
* [ ] Add search tests.

### Detail page

* [ ] Verify valid song detail page.
* [ ] Return 404 for missing song.
* [ ] Handle missing image.
* [ ] Handle missing audio.
* [ ] Confirm authenticated and anonymous behavior.
* [ ] Remove unrelated side effects from detail rendering.

### Quality

* [ ] Review query count.
* [ ] Remove obvious duplicate queries.
* [ ] Add pagination decision.
* [ ] Add browsing and search tests.
* [ ] Run full test suite.
* [ ] Commit and push.
* [ ] Review and merge.

## Exit criteria

* [ ] Browsing works end to end.
* [ ] Search behavior is defined.
* [ ] Language filters work.
* [ ] Detail pages are safe.
* [ ] Tests pass.

## Branch

`fix/browsing-and-search`

## Status

**Not started**

---

# Phase 6 — Local Authentication Recovery

## Goal

Make registration, login, logout, and protected operations reliable.

## Checklist

### Signup

* [ ] Verify valid signup.
* [ ] Verify duplicate username handling.
* [ ] Verify password validation.
* [ ] Verify password confirmation.
* [ ] Verify successful redirect.
* [ ] Improve error messages where needed.

### Login

* [ ] Verify valid login.
* [ ] Verify invalid username.
* [ ] Verify invalid password.
* [ ] Remove redundant authentication logic.
* [ ] Verify redirect behavior.
* [ ] Verify already-authenticated behavior.

### Logout

* [ ] Verify logout route.
* [ ] Verify session ends.
* [ ] Verify redirect destination.
* [ ] Confirm method choice is appropriate.

### Authorization

* [ ] Identify every user-specific view.
* [ ] Add server-side login protection.
* [ ] Do not rely on hidden template buttons.
* [ ] Verify anonymous users are redirected or rejected.
* [ ] Verify authenticated users can access permitted features.
* [ ] Verify CSRF protection.

### Tests

* [ ] Signup tests.
* [ ] Login tests.
* [ ] Logout tests.
* [ ] Protected-page tests.
* [ ] Anonymous mutation tests.
* [ ] Invalid-form tests.
* [ ] Full regression run.

## Exit criteria

* [ ] Local authentication works.
* [ ] Protected mutations require login.
* [ ] CSRF remains enabled.
* [ ] Tests cover authentication behavior.

## Branch

`fix/local-authentication`

## Status

**Not started**

---

# Phase 7 — Social Authentication Decision

## Goal

Decide whether Google login and django-allauth remain part of the project.

## Checklist

### Investigation

* [ ] Identify all django-allauth settings.
* [ ] Identify all allauth URLs.
* [ ] Identify social-login template elements.
* [ ] Identify all allauth dependencies.
* [ ] Confirm whether social login is currently functional.
* [ ] Document missing provider configuration.

### Product decision

* [ ] Decide whether Google login is required.
* [ ] Decide whether social login is needed for version 1.
* [ ] Decide whether local auth is sufficient initially.

### Keep option

* [ ] Update django-allauth safely.
* [ ] Configure Google provider through environment variables.
* [ ] Document Google OAuth setup.
* [ ] Test provider UI.
* [ ] Test failure behavior when credentials are absent.
* [ ] Keep secrets outside Git.

### Remove/defer option

* [ ] Remove broken social-login buttons.
* [ ] Remove unused provider configuration.
* [ ] Remove unused URL routes.
* [ ] Remove unused dependencies only after verification.
* [ ] Document social login as deferred.

## Exit criteria

* [ ] Authentication architecture is intentional.
* [ ] No broken OAuth links remain.
* [ ] Documentation matches actual behavior.

## Suggested branches

* `decision/social-authentication`
* `feature/google-auth`
* `refactor/remove-unused-allauth`

## Status

**Not started**

---

# Phase 8 — Favourites Recovery

## Goal

Make favourites secure, deterministic, and protected from duplicates.

## Checklist

* [ ] Inspect current Favourite model.
* [ ] Inspect favourite add behavior.
* [ ] Inspect favourite remove behavior.
* [ ] Protect mutations with login requirements.
* [ ] Validate song IDs.
* [ ] Prevent duplicate favourites.
* [ ] Decide whether `is_fav` is still necessary.
* [ ] Ensure users can modify only their own favourites.
* [ ] Replace fragile POST parsing.
* [ ] Use explicit form fields.
* [ ] Use POST-only mutation endpoints.
* [ ] Add CSRF-protected forms.
* [ ] Add empty favourites state.

### Tests

* [ ] Add favourite.
* [ ] Remove favourite.
* [ ] Duplicate add.
* [ ] Anonymous add.
* [ ] Anonymous remove.
* [ ] Invalid song.
* [ ] Cross-user isolation.
* [ ] Empty favourites page.

## Exit criteria

* [ ] Favourite operations are authenticated.
* [ ] Duplicate policy is enforced.
* [ ] Cross-user access is prevented.
* [ ] Tests pass.

## Branch

`fix/favourites`

## Status

**Not started**

---

# Phase 9 — Playlist Recovery

## Goal

Make playlist behavior secure and reliable before redesigning the model.

## Checklist

### Current model recovery

* [ ] Inspect Playlist model behavior.
* [ ] Fix `.distinct` to `.distinct()`.
* [ ] Replace fragile POST-key parsing.
* [ ] Validate playlist names.
* [ ] Validate song IDs.
* [ ] Require authentication.
* [ ] Ensure user ownership.
* [ ] Prevent duplicate song entries.
* [ ] Handle same playlist name across different users.
* [ ] Handle nonexistent playlists.
* [ ] Handle empty playlists.
* [ ] Add remove-song behavior if intended.
* [ ] Add delete-playlist behavior if intended.

### Tests

* [ ] Create playlist.
* [ ] Add song to playlist.
* [ ] Add duplicate song.
* [ ] View playlist.
* [ ] Empty playlist.
* [ ] Same playlist name for two users.
* [ ] Anonymous creation.
* [ ] Cross-user modification.
* [ ] Invalid song.
* [ ] Invalid playlist.

### Future redesign decision

* [ ] Document limitations of the current model.
* [ ] Decide whether to create separate `Playlist` and `PlaylistItem`.
* [ ] Defer schema redesign until current behavior is tested.

## Exit criteria

* [ ] Existing playlist behavior works safely.
* [ ] Ownership is enforced.
* [ ] Duplicate behavior is defined.
* [ ] Tests pass.

## Branch

`fix/playlists`

## Status

**Not started**

---

# Phase 10 — Playback and Recent History Recovery

## Goal

Define correct playback behavior and record recent history safely.

## Product decisions

* [ ] Decide whether anonymous users may play songs.
* [ ] Decide whether playback requires login.
* [ ] Decide what event counts as a play.
* [ ] Decide whether opening the detail page counts as a play.
* [ ] Decide whether repeated plays create repeated history entries.
* [ ] Decide recent-history limit.
* [ ] Decide whether users may clear history.
* [ ] Decide whether history needs timestamps.

## Technical recovery

* [ ] Find all playback routes.
* [ ] Find every history mutation.
* [ ] Remove state-changing behavior from GET requests.
* [ ] Use POST or a documented client event.
* [ ] Add method restrictions.
* [ ] Validate song existence.
* [ ] Add login protection where required.
* [ ] Add timestamps if approved.
* [ ] Define ordering.
* [ ] Handle deleted songs.
* [ ] Handle missing audio.
* [ ] Add empty recent-history state.
* [ ] Prevent unintended duplicates according to the approved policy.

### Tests

* [ ] Authenticated playback.
* [ ] Anonymous playback.
* [ ] GET request does not mutate history.
* [ ] POST creates history.
* [ ] Invalid song.
* [ ] Duplicate behavior.
* [ ] Ordering.
* [ ] History ownership.
* [ ] Empty history.
* [ ] Missing media.

## Exit criteria

* [ ] Playback semantics are documented.
* [ ] No history mutation happens through GET.
* [ ] History behavior is tested.
* [ ] Missing media is safe.

## Branch

`fix/playback-history-flow`

## Status

**Not started**

---

# Phase 11 — Baseline Recovery Test Suite

## Goal

Create a regression boundary before importing legacy work or modernizing dependencies.

## Checklist

### Test infrastructure

* [ ] Decide between Django TestCase and pytest-django.
* [ ] Add test helpers.
* [ ] Add test users.
* [ ] Add safe test song files.
* [ ] Add legal synthetic test media if needed.
* [ ] Add coverage configuration.
* [ ] Document the test command.

### Required test coverage

* [ ] Settings load.
* [ ] URLs reverse.
* [ ] Migrations are consistent.
* [ ] Homepage with no songs.
* [ ] Homepage with songs.
* [ ] Search.
* [ ] Language filters.
* [ ] Detail page.
* [ ] Missing song.
* [ ] Missing image.
* [ ] Missing audio.
* [ ] Signup.
* [ ] Login.
* [ ] Logout.
* [ ] Protected views.
* [ ] Favourites.
* [ ] Playlists.
* [ ] Playback.
* [ ] Recent history.
* [ ] Cross-user authorization.
* [ ] Invalid request methods.
* [ ] CSRF-sensitive operations.

### Recovery checkpoint

* [ ] Run complete test suite.
* [ ] Fix flaky tests.
* [ ] Record coverage.
* [ ] Document known gaps.
* [ ] Create recovery milestone commit.
* [ ] Tag recovery milestone as `recovery-v1`.

## Exit criteria

* [ ] Core features have regression coverage.
* [ ] Full suite passes.
* [ ] Behavior is safe to modernize.
* [ ] Recovery milestone is tagged.

## Branch

`test/core-recovery-suite`

## Status

**Not started**

---

# Phase 12 — Legacy Work Comparison and Recovery

## Goal

Review unfinished historical work and reintroduce only valuable changes.

## Checklist

### Compare files

* [ ] Compare legacy `musicapp/models.py`.
* [ ] Compare legacy `musicapp/views.py`.
* [ ] Inspect legacy migration `0006_song_play_count.py`.
* [ ] Compare legacy homepage template.
* [ ] Inspect `seed_songs.py`.
* [ ] Compare `requirements_clean.txt`.
* [ ] Document every meaningful difference.

### Evaluate play-count work

* [ ] Confirm whether `play_count` is wanted.
* [ ] Decide what counts as a play.
* [ ] Decide whether counts are aggregate or event-based.
* [ ] Decide how duplicate requests are handled.
* [ ] Decide anonymous-play behavior.
* [ ] Design tests.
* [ ] Create a fresh reviewed migration.
* [ ] Do not blindly copy the old migration.
* [ ] Implement play-count behavior.
* [ ] Add tests.

### Trending feature

* [ ] Decide whether trending songs are needed.
* [ ] Define ranking behavior.
* [ ] Define time window if applicable.
* [ ] Add homepage section.
* [ ] Handle zero plays.
* [ ] Add tests.

### Seed strategy

* [ ] Do not restore copyrighted songs.
* [ ] Decide on public-domain or synthetic demo media.
* [ ] Replace old seed script if necessary.
* [ ] Make seed operation explicit and repeatable.
* [ ] Document cleanup/reset behavior.

## Exit criteria

* [ ] Useful legacy work is recovered intentionally.
* [ ] No stale code is copied blindly.
* [ ] New migrations are reviewed.
* [ ] Tests pass.

## Suggested branches

* `feature/play-count`
* `feature/trending-songs`
* `chore/legal-demo-data`

## Status

**Not started**

---

# Phase 13 — Data Model Modernization

## Goal

Improve integrity, clarity, and scalability after recovery is stable.

## Checklist

### Playlist redesign

* [ ] Design normalized Playlist model.
* [ ] Design PlaylistItem model.
* [ ] Add playlist timestamps.
* [ ] Add playlist ownership.
* [ ] Add playlist privacy decision.
* [ ] Add uniqueness constraints.
* [ ] Plan data migration.
* [ ] Test migration.

### Favourite integrity

* [ ] Add unique constraint for user and song.
* [ ] Decide whether `is_fav` should be removed.
* [ ] Add migration.
* [ ] Test duplicate handling.

### Recent history

* [ ] Add timestamp.
* [ ] Add ordering.
* [ ] Add indexes.
* [ ] Define retention strategy.
* [ ] Add clear-history support if approved.

### Song model

* [ ] Add created and updated timestamps.
* [ ] Consider slug or UUID.
* [ ] Add validation for audio files.
* [ ] Add validation for cover images.
* [ ] Add file-size limits.
* [ ] Add ordering.
* [ ] Add useful indexes.
* [ ] Define deletion behavior.

### Migration safety

* [ ] Run dry-run migration checks.
* [ ] Review generated migrations.
* [ ] Add data migrations where needed.
* [ ] Test migrations from a fresh DB.
* [ ] Test migration rollback where practical.

## Exit criteria

* [ ] Schema is normalized where needed.
* [ ] Integrity constraints exist.
* [ ] Migrations are safe and tested.
* [ ] Existing behavior remains supported.

## Suggested branches

* `refactor/playlist-model`
* `refactor/favourite-integrity`
* `refactor/recent-history-model`
* `refactor/song-model`

## Status

**Not started**

---

# Phase 14 — Settings and Architecture Cleanup

## Goal

Remove duplicated configuration and improve maintainability.

## Checklist

### Settings

* [ ] Confirm `musicplayer.settings` is active.
* [ ] Audit `settings1/`.
* [ ] Decide whether `settings1/` should be removed.
* [ ] Choose one settings architecture.
* [ ] Separate development and production settings if needed.
* [ ] Centralize environment variables.
* [ ] Add safe production defaults.
* [ ] Add logging configuration.
* [ ] Document every environment variable.
* [ ] Add `.env.example` values for all required settings.

### Code organization

* [ ] Remove wildcard imports.
* [ ] Remove debug `print()` statements.
* [ ] Remove dead imports.
* [ ] Remove unused forms.
* [ ] Reduce repeated last-played logic.
* [ ] Extract reusable query helpers.
* [ ] Introduce service modules only where useful.
* [ ] Keep views small.
* [ ] Improve error handling.
* [ ] Remove commented-out obsolete code.

### Dependency cleanup

* [ ] Identify unused dependencies.
* [ ] Verify each dependency before removing it.
* [ ] Remove unused packages in focused commits.
* [ ] Reinstall from scratch.
* [ ] Run tests after every removal.

## Exit criteria

* [ ] One settings strategy exists.
* [ ] Environment configuration is documented.
* [ ] Repeated logic is reduced.
* [ ] Unused code and packages are removed.
* [ ] Tests pass.

## Branch

`refactor/settings-and-architecture`

## Status

**Not started**

---

# Phase 15 — Django and Dependency Modernization

## Goal

Upgrade to a supported Python and Django stack without breaking recovered behavior.

## Checklist

### Planning

* [ ] Select target Python version.
* [ ] Select target Django version.
* [ ] Select supported django-allauth version if retained.
* [ ] Audit all dependencies.
* [ ] Review Django release notes.
* [ ] Define incremental upgrade path.

### Python upgrade

* [ ] Create target Python environment.
* [ ] Install existing dependency set where possible.
* [ ] Resolve Python-specific incompatibilities.
* [ ] Run full tests.
* [ ] Document supported Python versions.

### Django upgrades

* [ ] Upgrade to an intermediate version if needed.
* [ ] Resolve deprecation warnings.
* [ ] Update settings.
* [ ] Update middleware.
* [ ] Update URL patterns.
* [ ] Update template usage.
* [ ] Update authentication packages.
* [ ] Run migrations checks.
* [ ] Run full tests after each upgrade.
* [ ] Continue until target supported Django version is reached.

### Requirements

* [ ] Remove obsolete packages.
* [ ] Separate production and development dependencies if useful.
* [ ] Create reproducible dependency files.
* [ ] Add dependency vulnerability scanning.
* [ ] Verify clean installation.

## Exit criteria

* [ ] Supported Python version is used.
* [ ] Supported Django version is used.
* [ ] Dependencies install reproducibly.
* [ ] Full test suite passes.
* [ ] Critical vulnerabilities are resolved.

## Suggested branches

* `upgrade/python-runtime`
* `upgrade/django-intermediate`
* `upgrade/django-lts`
* `build/clean-requirements`

## Status

**Not started**

---

# Phase 16 — UI and Branding Redesign

## Goal

Create a polished, original, responsive identity.

## Product decisions

* [ ] Choose final project name.
* [ ] Define logo direction.
* [ ] Define color palette.
* [ ] Define typography.
* [ ] Define visual tone.
* [ ] Define desktop and mobile navigation.
* [ ] Choose frontend approach.
* [ ] Decide whether to use Bootstrap 5, Tailwind, HTMX, or Alpine.js.
* [ ] Avoid introducing a separate SPA without justification.

## Branding cleanup

* [ ] Remove all remaining `GALVANIC` branding.
* [ ] Remove inherited visual references.
* [ ] Replace old favicon.
* [ ] Replace background images.
* [ ] Add original logo.
* [ ] Add legal demo artwork.

## Page redesign

* [ ] Base layout.
* [ ] Navigation.
* [ ] Homepage.
* [ ] Song library.
* [ ] Search results.
* [ ] Song detail.
* [ ] Player.
* [ ] Recent history.
* [ ] Favourites.
* [ ] Playlists.
* [ ] Login.
* [ ] Signup.
* [ ] Profile.
* [ ] Admin-facing presentation if needed.
* [ ] Error pages.
* [ ] Empty states.

## Accessibility

* [ ] Keyboard navigation.
* [ ] Visible focus states.
* [ ] Semantic buttons and links.
* [ ] Form labels.
* [ ] Error announcements.
* [ ] Color contrast.
* [ ] Accessible audio controls.
* [ ] Reduced-motion support.
* [ ] Responsive text and controls.

## Responsive testing

* [ ] Mobile.
* [ ] Tablet.
* [ ] Laptop.
* [ ] Large desktop.
* [ ] Long song names.
* [ ] Missing images.
* [ ] Empty content.
* [ ] Error states.

## Exit criteria

* [ ] Original branding exists.
* [ ] No inherited branding remains.
* [ ] Core pages are responsive.
* [ ] Accessibility checks pass.
* [ ] Current screenshots are created.

## Suggested branches

* `design/brand-system`
* `design/base-layout`
* `design/library`
* `design/player`
* `design/auth-pages`
* `design/mobile`

## Status

**Not started**

---

# Phase 17 — New Backend Capabilities

## Goal

Expand the recovered project into a stronger modern application.

## Feature candidates

### User features

* [ ] User profile.
* [ ] Avatar.
* [ ] Profile preferences.
* [ ] Listening statistics.
* [ ] Account deletion.
* [ ] Clear history.

### Playlist improvements

* [ ] Playlist descriptions.
* [ ] Playlist cover images.
* [ ] Playlist privacy.
* [ ] Playlist sharing.
* [ ] Playlist ordering.
* [ ] Collaborative playlist decision.

### Discovery

* [ ] Trending songs.
* [ ] Most played.
* [ ] Recently added.
* [ ] Improved search.
* [ ] Sorting.
* [ ] Filtering.
* [ ] Pagination.
* [ ] Recommendations decision.

### Media management

* [ ] Upload workflow.
* [ ] File validation.
* [ ] Metadata extraction.
* [ ] Admin review.
* [ ] Storage strategy.
* [ ] Deletion and cleanup.

### API

* [ ] Identify a real API consumer.
* [ ] Decide whether REST API is needed.
* [ ] Add Django REST Framework only if justified.
* [ ] Design authentication.
* [ ] Add serializers.
* [ ] Add API tests.
* [ ] Add API documentation.

### Reliability

* [ ] Rate limiting.
* [ ] Caching.
* [ ] Background jobs.
* [ ] Audit logging.
* [ ] Soft deletion.
* [ ] Analytics.

## Exit criteria

Defined individually for each approved feature.

## Status

**Not started**

---

# Phase 18 — Security Hardening

## Goal

Prepare the application for public deployment.

## Checklist

### Production settings

* [ ] Set `DEBUG=False`.
* [ ] Configure `ALLOWED_HOSTS`.
* [ ] Configure CSRF trusted origins.
* [ ] Set secure session cookies.
* [ ] Set secure CSRF cookies.
* [ ] Configure HTTPS redirect.
* [ ] Configure HSTS.
* [ ] Add security headers.
* [ ] Add safe error pages.
* [ ] Ensure secrets come only from environment variables.

### Authentication security

* [ ] Add login rate limiting.
* [ ] Review password reset flow.
* [ ] Review session duration.
* [ ] Review logout behavior.
* [ ] Review OAuth configuration.
* [ ] Protect admin.
* [ ] Test cross-user access.

### Upload security

* [ ] Validate extensions.
* [ ] Validate MIME type.
* [ ] Limit file size.
* [ ] Prevent path traversal.
* [ ] Rename uploaded files safely.
* [ ] Separate trusted and untrusted media.
* [ ] Add cleanup process.

### Application security

* [ ] Remove mutation through GET.
* [ ] Verify CSRF protection.
* [ ] Verify authorization.
* [ ] Review XSS risks.
* [ ] Review open redirects.
* [ ] Review SQL injection exposure.
* [ ] Review debug leakage.
* [ ] Run dependency audit.
* [ ] Run Django deployment checks.

## Exit criteria

* [ ] Production security checklist passes.
* [ ] Authorization tests pass.
* [ ] No secrets are committed.
* [ ] Uploads are validated.
* [ ] Dependency scan has no unaddressed critical issues.

## Branch

`security/production-hardening`

## Status

**Not started**

---

# Phase 19 — Performance and Reliability

## Goal

Improve responsiveness, scalability, and operational reliability.

## Checklist

### Database

* [ ] Identify N+1 queries.
* [ ] Add `select_related`.
* [ ] Add `prefetch_related`.
* [ ] Add database indexes.
* [ ] Add pagination.
* [ ] Review expensive search queries.
* [ ] Review history queries.

### Caching

* [ ] Decide whether caching is needed.
* [ ] Cache safe read-heavy pages.
* [ ] Define invalidation.
* [ ] Avoid premature complexity.

### Media

* [ ] Decide media delivery strategy.
* [ ] Configure cloud/object storage if approved.
* [ ] Add CDN decision.
* [ ] Optimize cover images.
* [ ] Add upload limits.

### Reliability

* [ ] Add health endpoint.
* [ ] Add structured logging.
* [ ] Add error monitoring.
* [ ] Add database backup plan.
* [ ] Add rollback plan.
* [ ] Handle missing media gracefully.
* [ ] Configure production timeouts.
* [ ] Test failure scenarios.

## Exit criteria

* [ ] Major N+1 issues are fixed.
* [ ] Key pages remain responsive.
* [ ] Health check works.
* [ ] Logging and monitoring exist.
* [ ] Backup and rollback strategy are documented.

## Status

**Not started**

---

# Phase 20 — Continuous Integration and Repository Quality

## Goal

Automate testing, quality, and security checks.

## Checklist

### GitHub Actions

* [ ] Install dependencies.
* [ ] Configure environment variables for tests.
* [ ] Run `python manage.py check`.
* [ ] Run migration drift check.
* [ ] Run test suite.
* [ ] Run coverage.
* [ ] Run linting.
* [ ] Run formatting check.
* [ ] Run dependency audit.
* [ ] Cache dependencies where appropriate.

### Tooling

* [ ] Add Ruff.
* [ ] Add Black.
* [ ] Add coverage.
* [ ] Add pip-audit.
* [ ] Add pre-commit if useful.
* [ ] Document local quality commands.

### Repository workflow

* [ ] Add pull-request template.
* [ ] Add issue templates.
* [ ] Add contribution guide.
* [ ] Add branch protection recommendations.
* [ ] Require passing CI before merge.
* [ ] Define review checklist.

## Exit criteria

* [ ] Pull requests run automated checks.
* [ ] Failing tests prevent merge.
* [ ] Migration drift is detected.
* [ ] Basic security scanning exists.
* [ ] Local and CI commands match.

## Branch

`ci/quality-pipeline`

## Status

**Not started**

---

# Phase 21 — Deployment Preparation

## Goal

Deploy the application reproducibly and securely.

## Hosting decision

* [ ] Compare Render.
* [ ] Compare Railway.
* [ ] Compare Fly.io.
* [ ] Compare VPS.
* [ ] Select hosting provider.
* [ ] Select production database.
* [ ] Select media-storage provider.

## Deployment configuration

* [ ] Add production server.
* [ ] Add production requirements.
* [ ] Add startup command.
* [ ] Add static-file handling.
* [ ] Add media-storage configuration.
* [ ] Add environment-variable documentation.
* [ ] Add release migration command.
* [ ] Add health check.
* [ ] Add Dockerfile if useful.
* [ ] Add `.dockerignore`.
* [ ] Add deployment config.
* [ ] Add rollback process.

## Production setup

* [ ] Configure production database.
* [ ] Configure secrets.
* [ ] Configure domain.
* [ ] Configure HTTPS.
* [ ] Configure allowed hosts.
* [ ] Configure CSRF origins.
* [ ] Configure logging.
* [ ] Configure monitoring.
* [ ] Configure backups.
* [ ] Create production admin securely.
* [ ] Add legal demonstration data.

## Deployment verification

* [ ] Application starts.
* [ ] Migrations run.
* [ ] Static files load.
* [ ] Media works.
* [ ] Health check passes.
* [ ] Signup works.
* [ ] Login works.
* [ ] Core pages work.
* [ ] Security settings are active.
* [ ] Logs contain no secrets.

## Exit criteria

* [ ] Deployment can be reproduced from GitHub.
* [ ] Production configuration is secure.
* [ ] Database and media persist correctly.
* [ ] Health and monitoring work.
* [ ] Rollback plan exists.

## Suggested branch

`deploy/<provider-name>`

## Status

**Not started**

---

# Phase 22 — Final Documentation and Portfolio Presentation

## Goal

Present the project as a professional engineering and recovery case study.

## README

* [ ] Final project name.
* [ ] Project overview.
* [ ] Live demo.
* [ ] Screenshots.
* [ ] Features.
* [ ] Technology stack.
* [ ] Architecture.
* [ ] Local setup.
* [ ] Environment variables.
* [ ] Database setup.
* [ ] Testing.
* [ ] Deployment.
* [ ] Security considerations.
* [ ] Roadmap.
* [ ] License.
* [ ] Media policy.
* [ ] Recovery story.
* [ ] Modernization summary.
* [ ] Known limitations.

## Technical documentation

* [ ] Architecture diagram.
* [ ] Database relationship diagram.
* [ ] Authentication flow.
* [ ] Playback flow.
* [ ] Deployment diagram.
* [ ] API documentation if applicable.
* [ ] Engineering decisions.
* [ ] Changelog.
* [ ] Contribution guide.
* [ ] Recovery audit archive.

## Portfolio case study

* [ ] Describe the inherited state.
* [ ] Describe the recovery challenges.
* [ ] Explain legal and repository cleanup.
* [ ] Explain runtime restoration.
* [ ] Explain security improvements.
* [ ] Explain schema decisions.
* [ ] Explain testing improvements.
* [ ] Add before-and-after screenshots.
* [ ] Add measurable results.
* [ ] Add lessons learned.

## Release

* [ ] Verify all tests pass.
* [ ] Verify CI passes.
* [ ] Verify production deployment.
* [ ] Verify documentation.
* [ ] Create release notes.
* [ ] Create GitHub release.
* [ ] Tag `v1.0.0`.
* [ ] Make repository public if appropriate.
* [ ] Add project to portfolio.

## Exit criteria

* [ ] Professional README exists.
* [ ] Live demo works.
* [ ] Current screenshots exist.
* [ ] Setup instructions are complete.
* [ ] Portfolio case study is ready.
* [ ] Version `v1.0.0` is released.

## Status

**Not started**

---

# Overall Progress Dashboard

| Phase | Name                                           | Status          |
| ----- | ---------------------------------------------- | --------------- |
| 0     | Repository Preservation and Governance         | Nearly complete |
| 1     | Runtime Environment Verification               | Not started     |
| 2     | Dependency and Startup Restoration             | Not started     |
| 3     | Disposable Local Database Setup                | Not started     |
| 4     | Empty Library and Missing Media Safety         | Not started     |
| 5     | Core Browsing and Search Recovery              | Not started     |
| 6     | Local Authentication Recovery                  | Not started     |
| 7     | Social Authentication Decision                 | Not started     |
| 8     | Favourites Recovery                            | Not started     |
| 9     | Playlist Recovery                              | Not started     |
| 10    | Playback and Recent History Recovery           | Not started     |
| 11    | Baseline Recovery Test Suite                   | Not started     |
| 12    | Legacy Work Comparison and Recovery            | Not started     |
| 13    | Data Model Modernization                       | Not started     |
| 14    | Settings and Architecture Cleanup              | Not started     |
| 15    | Django and Dependency Modernization            | Not started     |
| 16    | UI and Branding Redesign                       | Not started     |
| 17    | New Backend Capabilities                       | Not started     |
| 18    | Security Hardening                             | Not started     |
| 19    | Performance and Reliability                    | Not started     |
| 20    | Continuous Integration and Repository Quality  | Not started     |
| 21    | Deployment Preparation                         | Not started     |
| 22    | Final Documentation and Portfolio Presentation | Not started     |

---

# Current Immediate Actions

* [ ] Commit and push `SYSTEM_RECOVERY_ANALYSIS.md`.
* [ ] Paste the Codex Master Context into the Codex project chat.
* [ ] Give Codex the runtime-verification assignment.
* [ ] Review Codex’s planned commands before modifications.
* [ ] Run `py -0p`.
* [ ] Create a compatible `.venv`.
* [ ] Attempt dependency installation.
* [ ] Generate `RUNTIME_VERIFICATION_REPORT.md`.
* [ ] Review the report with ChatGPT.
* [ ] Convert the first confirmed blocker into the first implementation task.

---

# Completion Definition

The project is complete when:

* [ ] Supported Python and Django versions are used.
* [ ] Dependencies install reproducibly.
* [ ] All migrations are stable.
* [ ] Core tests pass.
* [ ] CI passes.
* [ ] Empty states work.
* [ ] Missing media is handled gracefully.
* [ ] Authentication is secure.
* [ ] User data is isolated.
* [ ] Media usage is legal.
* [ ] UI is original and responsive.
* [ ] Production settings are secure.
* [ ] Deployment is repeatable.
* [ ] Documentation is complete.
* [ ] Release `v1.0.0` is published.
