# Django 4.2 Upgrade

## Runtime

- Python executable: `.venv-django42\Scripts\python.exe`.
- Python version: 3.12.3.
- Django version: 4.2.30.
- django-allauth version: 65.11.2.
- Pillow version: 10.4.0.

This phase used only `.venv-django42`. The old local `.venv` and the Django
3.2 `.venv-django32` environment were not used for installation or verification.

## Dependency File

Created `requirements-django42.txt` as a direct-dependency file for this
intermediate runtime.

Direct dependencies selected:

- `Django==4.2.30`: latest observed Django 4.2 patch release and compatible
  with Python 3.12.
- `django-allauth==65.11.2`: compatible with Django 4.2 and Python 3.12 while
  avoiding newer 2026 allauth feature changes during this intermediate step.
- `django-crispy-forms==1.14.0`: retained because `crispy_forms` remains in
  `INSTALLED_APPS`.
- `Pillow==10.4.0`: Python 3.12-compatible media/image dependency.
- `python-decouple==3.8`: active settings dependency.
- `requests-oauthlib==2.0.0`: OAuth provider support for allauth social auth.
- `python3-openid==3.2.0`: OpenID provider support retained for allauth.
- `PyJWT==2.10.1`: required by the Google provider JWT import path.
- `cryptography==45.0.7`: required by the Google provider JWT helper.

## Dependencies Removed or Deferred

The Django 4.2 file does not directly pin legacy transitive packages such as
`asgiref`, `certifi`, `cffi`, `defusedxml`, `idna`, `oauthlib`, `requests`,
`sqlparse`, `tzdata`, or `urllib3`.

Apparently unused dependencies remain excluded from the new direct runtime set:

- `argon2-cffi`
- `django-debug-toolbar`
- `django-environ`
- `django-model-utils`
- `django-redis`
- `djangorestframework`
- `python-slugify`

## Copied Legacy Database Rehearsal

The real SQLite database remained at:

`C:\Users\polma\Desktop\django_music_player\music-player-recovery\db.sqlite3`

Original file size: `266240` bytes.

A temporary copy was created outside the repository at:

`C:\Users\polma\AppData\Local\Temp\sonica_legacy_django42_v6cah72w.sqlite3`

The copy was migrated, queried, and deleted after verification.

## Row Counts

Counts before applying Django/allauth third-party migrations to the copied DB:

| Table | Count |
| --- | ---: |
| `auth_user` | 1 |
| `musicapp_song` | 8 |
| `musicapp_favourite` | 0 |
| `musicapp_playlist` | 0 |
| `musicapp_recent` | 1 |
| `account_emailaddress` | 0 |
| `socialaccount_socialaccount` | 0 |
| `socialaccount_socialapp` | 0 |

Counts after migration were identical. `PRAGMA integrity_check` returned `ok`.

## Third-Party Migrations Applied on the Copy

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

Repeated migration on the copied DB reported no planned operations and no
migrations to apply.

## Copied DB Application Checks

On the migrated copy:

- temporary local login succeeded,
- profile returned 200,
- favourite returned 200,
- playlist returned 200,
- recent returned 200.

Only aggregate counts and route statuses were recorded. No password hashes,
tokens, OAuth keys, or private user data were documented.

## Compatibility Findings

Initial Django 4.2 checks, tests, and smoke passed before code changes.

One settings cleanup was made:

- Removed `USE_L10N` from active `musicplayer.settings` because Django 4.x no
  longer uses it.

No allauth settings were changed. The existing allauth middleware from the
Django 3.2 phase remains required and valid.

## Fresh Database Results

A temporary SQLite database was created outside the repository, migrated from
zero, seeded twice, tested, smoke-tested, and removed.

- Fresh migration from zero: succeeded.
- First `seed_demo_data`: 8 songs created.
- Second `seed_demo_data`: 8 unchanged.
- Song counts after seed runs: `8,8`.
- Tests on fresh DB flow: 97 passed.
- Smoke checks on fresh DB flow: 27 passed, overall PASS.

## Warnings

`python -Wd manage.py check` and `python -Wd manage.py test` emitted no warnings.

Deferred areas for later phases:

- allauth setting modernization for the final allauth target,
- production settings hardening,
- optional future replacement of legacy `settings1/`.

## Verification Results

- `python -c "import sys; print(sys.executable)"`: confirmed
  `.venv-django42\Scripts\python.exe`.
- `python --version`: Python 3.12.3.
- `python -m django --version`: 4.2.30.
- `python -m pip check`: passed.
- `python manage.py check`: passed.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- `python manage.py test`: 97 tests passed.
- `python manage.py project_smoke_test`: 27 checks passed, overall PASS.
- `python -Wd manage.py check`: passed with no warnings.
- `python -Wd manage.py test`: 97 tests passed with no warnings.

## Rollback Instructions

1. Remove `requirements-django42.txt`.
2. Restore `USE_L10N = True` in `musicplayer/settings.py` only if returning to a
   Django 3.x runtime that requires it.
3. Remove this document and revert the roadmap status update.
4. Delete `.venv-django42` if the environment itself should be discarded.

No Sonica migrations or repository database changes need to be rolled back.

## Exact Next Branch

`modernization/django-52-upgrade`
