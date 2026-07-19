# Modernization Roadmap

## Phase 1: Django Compatibility Prep

Branch: `modernization/django-compat-prep`

- Status: in preparation on this branch; this does not complete the actual
  Django runtime upgrade.
- Replace `is_safe_url` with a centralized compatibility helper that uses
  `url_has_allowed_host_and_scheme`.
- Keep `USE_L10N` behavior unchanged on Django 3.0 and document later removal.
- Audit allauth settings against the intended target version.
- Keep Django 3.0.8 while making compatibility changes.
- Gate: full test suite and smoke harness pass.

## Phase 2: Dependency Cleanup

Branch: `modernization/dependency-cleanup`

- Status: complete on `modernization/dependency-cleanup`; `requirements.txt`
  is now the canonical Django 5.2 runtime file.
- Remove unused packages only after confirming they are not imported.
- Separate direct requirements from transitive dependencies.
- Add a repeatable dependency resolution process.
- Gate: clean environment install, full tests, smoke harness.

## Phase 3: Settings Hardening

Branch: `modernization/settings-hardening`

- Status: settings entry-point cleanup complete on
  `modernization/settings-cleanup`; production security hardening complete on
  `modernization/production-hardening`.
- Make production settings explicit.
- Add environment-driven allowed hosts, CSRF origins, secure cookies, and static
  configuration.
- Quarantine or remove legacy `settings1/` modules.
- Gate: local and test settings still pass all checks.

## Phase 4: Django Runtime Upgrade

Branch: `modernization/django-upgrade`

- Status: Django 3.2 intermediate upgrade complete on
  `modernization/django-32-upgrade`; Django 4.2 intermediate upgrade complete
  on `modernization/django-42-upgrade`; final Django 5.2 LTS runtime upgrade
  complete on `modernization/django-52-upgrade`.
- Upgrade through supported Django versions incrementally.
- Update allauth and related dependencies in lockstep.
- Run migrations and template tests at each step.
- Gate: tests, smoke harness, and manual browser QA.

## Phase 5: Data Integrity Migration

Branch: `modernization/data-integrity`

- Add uniqueness constraints for favourites and temporary playlist membership if
  the current model still exists.
- Add indexes for user-scoped queries.
- Add data cleanup migrations for duplicates before constraints.
- Gate: duplicate detection, migration dry run, migration apply on copied data.

## Phase 6: Playlist Model Redesign

Branch: `modernization/playlist-containers`

- Status: schema foundation complete on `modernization/playlist-schema`; data
  migration complete on `modernization/playlist-data-migration`; view/template
  cutover remains deferred.
- Introduce a true playlist container model and membership table.
- Preserve current playlist names and song memberships through a data migration.
- Support empty playlists intentionally.
- Gate: migration tests, authorization tests, browser QA.

## Phase 7: Upload and Media Validation

Branch: `modernization/media-validation`

- Add file extension, size, and content validation.
- Decide storage behavior for production.
- Preserve missing-media fallbacks.
- Gate: malicious/invalid upload tests and admin smoke tests.

## Phase 8: Observability

Branch: `modernization/observability`

- Status: platform-neutral deployment readiness complete on
  `modernization/deployment-readiness`; provider-specific deployment remains
  deferred.
- Add logging configuration and release smoke reporting.
- Add deployment health checks if needed.
- Gate: logs visible locally and in the chosen deployment environment.

## Phase 9: Frontend Certification

Branch: `modernization/frontend-certification`

- Browser-test Sonica's redesigned pages and player shell across desktop and
  mobile sizes.
- Verify media fallback states, authenticated navigation, and collection pages.
- Gate: screenshot/manual QA evidence plus existing backend checks.
