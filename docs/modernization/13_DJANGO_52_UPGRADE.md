# Django 5.2 LTS Upgrade

## Runtime

- Python executable: `.venv-django52\Scripts\python.exe`.
- Python version: 3.12.3.
- Django version: 5.2.16.
- django-allauth version: 65.18.0.
- Pillow version: 11.3.0.

This is now the supported local framework/runtime baseline. The older `.venv`,
`.venv-django32`, and `.venv-django42` environments remain rollback/reference
evidence only.

## Direct Dependencies

Created `requirements-django52.txt` as the final direct-dependency file.

| Dependency | Version | Rationale |
| --- | ---: | --- |
| Django | 5.2.16 | Current supported Django 5.2 LTS patch release. |
| django-allauth | 65.18.0 | Current stable allauth release supporting Django 5.2 and Python 3.12. |
| django-crispy-forms | 1.14.0 | Retained because `crispy_forms` remains in `INSTALLED_APPS`; removal is deferred. |
| Pillow | 11.3.0 | Stable Python 3.12-compatible image dependency with security fixes. |
| python-decouple | 3.8 | Active settings loader. |
| requests-oauthlib | 2.0.0 | OAuth provider support for allauth social authentication. |
| python3-openid | 3.2.0 | OpenID provider support retained with allauth. |
| PyJWT | 2.10.1 | Required by allauth Google provider import path. |
| cryptography | 45.0.7 | Required by allauth Google provider JWT helper. |

Transitive packages such as `asgiref`, `certifi`, `cffi`, `requests`,
`sqlparse`, `tzdata`, and `urllib3` are intentionally not directly pinned.

Deferred legacy dependencies:

- `argon2-cffi`
- `django-debug-toolbar`
- `django-environ`
- `django-model-utils`
- `django-redis`
- `djangorestframework`
- `python-slugify`

## Compatibility Evidence

- Django 5.2 is an LTS release and supports Python 3.12.
- The Django release index lists the 5.2 patch series through 5.2.16.
- django-allauth 65.18.0 metadata lists Python 3.10+ and Django 5.2 support.
- Pillow documentation lists Python 3.12 support for Pillow 11.

## Initial Failures

No initial Django 5.2 application failures occurred. Before source edits:

- `manage.py check`: passed.
- `makemigrations --check --dry-run`: no changes detected.
- `manage.py test`: 97 tests passed.
- `recovery_smoke_test`: 27 checks passed.
- `python -Wd manage.py check`: no warnings.
- `python -Wd manage.py test`: no warnings.

## Django Compatibility Changes

- Removed the dead `is_safe_url` fallback from `authentication.compat`; Django
  5.2 uses `url_has_allowed_host_and_scheme` directly.
- Updated `README.md` setup and verification commands to use Python 3.12 and
  `requirements-django52.txt`.

No models, migrations, playlist behavior, recent-history behavior, playback GET
mutations, upload validation, production settings, or frontend design were
changed.

## Allauth Setting Decision

The selected allauth version resolved the current configuration to the intended
behavior:

- login methods: username;
- signup fields: email, username, password1, password2;
- email verification: none.

No allauth setting changes were required because checks and warning audits were
clean and the existing local auth tests preserved behavior.

| Old setting | New setting | Behavior preserved | Test coverage |
| --- | --- | --- | --- |
| `ACCOUNT_EMAIL_VERIFICATION = 'none'` | No change | Local signup does not require email verification. | Signup/authentication tests. |
| `SOCIALACCOUNT_QUERY_EMAIL = True` | No change | Google provider can still request email while optional Google auth remains hidden until configured. | Google-hidden tests and provider import rehearsal. |
| `SOCIALACCOUNT_PROVIDERS['google']` | No change | Existing Google scope/auth params preserved. | Provider import rehearsal. |
| `ENABLE_GOOGLE_AUTH` | No change | Google UI remains disabled by default and hidden without `SocialApp`. | Authentication template tests. |

## Compatibility Helper Decision

Django 5.2 is now the supported runtime, so the old `is_safe_url` fallback was
removed. Redirect validation remains centralized in
`authentication.compat.get_safe_redirect_url()` and still uses
`url_has_allowed_host_and_scheme`.

Existing redirect tests continue to cover:

- relative internal redirects,
- same-host redirects,
- external redirects,
- protocol-relative external redirects,
- malformed URLs,
- HTTPS requests rejecting unsafe HTTP redirects.

## Copied Legacy Database Rehearsal

The real database remained at:

`C:\Users\polma\Desktop\django_music_player\music-player-recovery\db.sqlite3`

Original file size: `266240` bytes.

A temporary copy was created outside the repository:

`C:\Users\polma\AppData\Local\Temp\sonica_legacy_django52_jjc0j4gl.sqlite3`

The copy was migrated, queried, and deleted after verification.

## Copied Database Counts

| Table | Before | After |
| --- | ---: | ---: |
| `auth_user` | 1 | 1 |
| `musicapp_song` | 8 | 8 |
| `musicapp_favourite` | 0 | 0 |
| `musicapp_playlist` | 0 | 0 |
| `musicapp_recent` | 1 | 1 |
| `account_emailaddress` | 0 | 0 |
| `socialaccount_socialaccount` | 0 | 0 |
| `socialaccount_socialapp` | 0 | 0 |

`PRAGMA integrity_check` returned `ok`.

## Third-Party Migrations Applied

- `account.0003_alter_emailaddress_create_unique_verified_email`
- `account.0004_alter_emailaddress_drop_unique_email`
- `account.0005_emailaddress_idx_upper_email`
- `account.0006_emailaddress_lower`
- `account.0007_emailaddress_idx_email`
- `account.0008_emailaddress_unique_primary_email_fixup`
- `account.0009_emailaddress_unique_primary_email`
- `auth.0012_alter_user_first_name_max_length`
- `socialaccount.0004_app_provider_id_settings`
- `socialaccount.0005_socialtoken_nullable_app`
- `socialaccount.0006_alter_socialaccount_extra_data`

Repeated migration on the copied database reported no planned operations and no
migrations to apply.

Copied DB probes:

- temporary local login succeeded,
- profile returned 200,
- favourite returned 200,
- playlist returned 200,
- recent returned 200,
- Google provider import succeeded.

No password hashes, tokens, OAuth keys, email addresses, or private user data
were recorded.

## Fresh Database Results

A temporary SQLite database was created outside the repository, migrated from
zero, seeded twice, tested, smoke-tested, and removed.

- Fresh migration from zero: succeeded.
- First `seed_demo_data`: 8 songs created.
- Second `seed_demo_data`: 8 unchanged.
- Song counts after seed runs: `8,8`.
- Tests: 97 passed.
- Smoke checks: 27 passed, overall PASS.

## Warning Audit

`python -Wd manage.py check` and `python -Wd manage.py test` emitted no warnings.

## Remaining Deferred Work

- Production settings hardening.
- Dependency cleanup and removal of unused packages.
- Legacy `settings1/` cleanup.
- Playlist container redesign.
- Recent/history redesign decisions.
- Playback GET mutation redesign.
- Upload validation.
- Logging and monitoring.

## Verification Results

- `python -c "import sys; print(sys.executable)"`: confirmed
  `.venv-django52\Scripts\python.exe`.
- `python --version`: Python 3.12.3.
- `python -m django --version`: 5.2.16.
- `python -m pip check`: passed.
- `python manage.py check`: passed.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- `python manage.py test`: 97 tests passed.
- `python manage.py recovery_smoke_test`: 27 checks passed, overall PASS.
- `python -Wd manage.py check`: passed with no warnings.
- `python -Wd manage.py test`: 97 tests passed with no warnings.

## Rollback Instructions

1. Remove `requirements-django52.txt`.
2. Restore the previous `authentication.compat` fallback if returning to a
   pre-5.2 compatibility branch.
3. Restore README setup commands to the selected older runtime if rolling back.
4. Remove this document and revert the roadmap status update.
5. Delete `.venv-django52` if the environment itself should be discarded.

No Sonica migrations or repository database changes need to be rolled back.

## Exact Next Branch

`modernization/dependency-cleanup`
