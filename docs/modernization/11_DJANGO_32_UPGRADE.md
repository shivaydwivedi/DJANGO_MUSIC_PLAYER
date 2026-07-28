# Django 3.2 Upgrade

## Runtime

- Python executable: `.venv-django32\Scripts\python.exe`.
- Python version: 3.10.11.
- Django version: 3.2.25.
- django-allauth version: 0.63.6.
- Pillow version: 10.4.0.

This phase used only `.venv-django32`. The old local `.venv` was not used for
installation or verification.

## Dependency File

Created `requirements-django32.txt` as a simple direct-dependency file for this
intermediate runtime. A nested `requirements/` structure is deferred until the
final target runtime is chosen.

Direct dependencies selected:

- `Django==3.2.25`: latest Django 3.2 patch release.
- `django-allauth==0.63.6`: last allauth line before later releases dropped
  Django 3.2 support.
- `django-crispy-forms==1.14.0`: retained because `crispy_forms` remains in
  `INSTALLED_APPS` and `CRISPY_TEMPLATE_PACK` is configured.
- `Pillow==10.4.0`: Python 3.10-compatible image library retained for media
  handling readiness.
- `python-decouple==3.8`: active settings dependency.
- `requests-oauthlib==2.0.0`: direct provider dependency for allauth social
  OAuth flows.
- `python3-openid==3.2.0`: allauth/social account provider dependency.
- `PyJWT==2.10.1`: required by allauth's Google provider import path.
- `cryptography==45.0.7`: required by allauth's Google provider JWT helper.

## Excluded Legacy Dependencies

The Django 3.2 file does not directly pin old transitive packages from the
legacy `requirements.txt`, including `asgiref`, `certifi`, `cffi`, `chardet`,
`defusedxml`, `idna`, `oauthlib`, `pycparser`, `pytz`, `requests`, `six`,
`sqlparse`, `text-unidecode`, and `urllib3`.

It also excludes packages that remain apparently unused in active runtime code:

- `argon2-cffi`
- `django-debug-toolbar`
- `django-environ`
- `django-model-utils`
- `django-redis`
- `djangorestframework`
- `python-slugify`

## Compatibility Failures Encountered

Initial checks found two startup failures:

1. `allauth.account.middleware.AccountMiddleware` was required by the selected
   allauth version.
2. The Google provider import path required `jwt` and `cryptography`.

Both failures were fixed without changing application business logic.

## Code Changes Made

- Added `allauth.account.middleware.AccountMiddleware` after Django's
  authentication middleware.
- Added `DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'` to preserve existing
  primary-key behavior and avoid Django 3.2 migration churn.

No models, migrations, playlist behavior, recent-history behavior, playback
mutation behavior, uploads, production settings, or frontend design were changed.

## Allauth Verification

Existing tests confirm:

- local signup works,
- local login works,
- logout remains POST-only,
- profile remains protected,
- Google buttons remain hidden when disabled,
- Google buttons remain hidden when no `SocialApp` exists,
- allauth URLs remain mounted at `accounts/`.

The upgraded allauth dependency imports successfully with the added provider
dependencies.

## Migration Results

- `makemigrations --check --dry-run`: no changes detected.
- `showmigrations`: existing project migrations load under Django 3.2.
- `migrate --plan` on the existing local SQLite database shows pending
  third-party migrations from upgraded Django/allauth packages:
  - `account.0003` through `account.0009`
  - `auth.0012`
  - `socialaccount.0004` through `socialaccount.0006`
- No Sonica app migrations were created.
- A fresh temporary SQLite database migrated from zero successfully.

The user's real local database was not overwritten.

## Fresh Database and Seed Results

A temporary SQLite database was created outside the repository, migrated from
zero, seeded twice, smoke-tested, and removed.

- First `seed_demo_data`: 8 created.
- Second `seed_demo_data`: 8 unchanged.
- Song counts after the two seed runs: `8,8`.
- Smoke harness on the temporary database: 27 checks passed, overall PASS.

## Warnings Remaining

`python -Wd manage.py check` and `python -Wd manage.py test` produced no
deprecation warnings in this environment.

Deferred warning-sensitive areas for later phases:

- `USE_L10N` removal for Django 4.x+.
- allauth setting modernization for the final allauth target.
- production settings hardening.

## Verification Results

- `python -c "import sys; print(sys.executable)"`: confirmed
  `.venv-django32\Scripts\python.exe`.
- `python --version`: Python 3.10.11.
- `python -m django --version`: 3.2.25.
- `python -m pip check`: passed.
- `python manage.py check`: passed.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- `python manage.py test`: 97 tests passed.
- `python manage.py project_smoke_test`: 27 checks passed, overall PASS.
- `python -Wd manage.py check`: passed with no warnings.
- `python -Wd manage.py test`: 97 tests passed with no warnings.

## Rollback Instructions

1. Remove `requirements-django32.txt`.
2. Remove `DEFAULT_AUTO_FIELD` and `allauth.account.middleware.AccountMiddleware`
   from `musicplayer/settings.py`.
3. Remove this document and revert the roadmap status update.
4. Delete `.venv-django32` if the environment itself should be discarded.

No migrations or database changes need to be rolled back from the repository.

## Exact Next Branch

`modernization/django-42-upgrade`
