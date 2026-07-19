# Django Compatibility Preparation

## Current Runtime

- Python: 3.8.10.
- Django: 3.0.8.
- django-allauth: 0.42.0.
- Active settings module: `musicplayer.settings`.
- Package versions were not changed in this phase.

## Confirmed Compatibility Blockers

| Finding | Location | Classification | Decision |
| --- | --- | --- | --- |
| `django.utils.http.is_safe_url` | `authentication.views` | Safe to replace now | Replaced with a compatibility helper using `url_has_allowed_host_and_scheme` where available. |
| `USE_L10N` | `musicplayer.settings`, `musicplayer/settings1/base.py` | Must wait for Django upgrade | Kept to preserve Django 3.0 formatting behavior; documented for later removal. |
| `SOCIALACCOUNT_QUERY_EMAIL` | active and legacy settings | Must wait for allauth upgrade | Kept for current allauth; transition documented below. |
| Legacy `settings1/` modules | `musicplayer/settings1/` | Must wait for settings-modernization phase | Not imported by default; documented but not deleted. |

## Blockers Fixed in This Phase

`is_safe_url` was removed from runtime imports. Redirect validation is now
centralized in `authentication.compat.get_safe_redirect_url()`, which uses
`url_has_allowed_host_and_scheme` on the current Django 3.0.8 baseline and falls
back to the older function only if needed.

The helper:

- accepts relative internal URLs,
- accepts same-host absolute URLs when the scheme is appropriate,
- rejects external hosts,
- rejects protocol-relative external URLs,
- rejects malformed URLs,
- respects `request.is_secure()` by requiring HTTPS redirects for HTTPS
  requests,
- returns `None` for missing or unsafe `next` values.

## Blockers Deliberately Deferred

- `USE_L10N` remains enabled because Django 3.0 still honors it and this phase
  must not change date, number, or template formatting.
- `SOCIALACCOUNT_QUERY_EMAIL` and current allauth provider settings remain
  unchanged until the allauth package is upgraded.
- `settings1/` remains in place until the settings-modernization phase can
  either delete it or replace it with a tested settings package.
- Playback GET mutations, playlist model redesign, upload validators,
  PostgreSQL setup, dependency cleanup, and deployment hardening are explicitly
  out of scope.

## Allauth Setting Transition Map

| Current setting | Current purpose | Future replacement | Upgrade phase | Risk |
| --- | --- | --- | --- | --- |
| `INSTALLED_APPS`: `allauth`, `allauth.account`, `allauth.socialaccount`, Google provider | Mount account and optional Google social auth models/templates | Keep if social auth remains; verify required extras and app list for target allauth | allauth-upgrade | Medium |
| `AUTHENTICATION_BACKENDS`: Django model backend plus allauth backend | Preserve local login while enabling allauth authentication | Keep both unless local-only auth is chosen | allauth-upgrade | Low |
| `django.template.context_processors.request` | Required by allauth template tags and request-aware flows | Keep | compatibility-prep | Low |
| `SITE_ID = 1` | Required by Django sites/allauth SocialApp lookup | Keep unless allauth/site strategy changes | settings-hardening | Low |
| `ACCOUNT_EMAIL_VERIFICATION = 'none'` | Allows local signup without email verification | Re-evaluate with `ACCOUNT_SIGNUP_FIELDS` and target signup policy | allauth-upgrade | Medium |
| `SOCIALACCOUNT_QUERY_EMAIL = True` | Requests email from social providers in older allauth | Prefer provider scopes and target allauth's account/signup field settings; verify against chosen allauth release | allauth-upgrade | Medium |
| `SOCIALACCOUNT_PROVIDERS['google']['SCOPE']` | Requests Google profile and email scopes | Keep or migrate to target provider config format if release notes require it | allauth-upgrade | Low |
| `SOCIALACCOUNT_PROVIDERS['google']['AUTH_PARAMS']` | Requests offline access | Keep only if refresh-token behavior is needed | allauth-upgrade | Medium |
| `ENABLE_GOOGLE_AUTH` | Project-specific feature flag hiding Google UI unless configured | Keep; not an allauth setting | compatibility-prep | Low |
| `SocialApp.objects.filter(provider='google').exists()` | Prevents rendering unusable Google buttons | Keep until provider configuration is redesigned | compatibility-prep | Low |

Local signup, local login, profile editing, and optional hidden Google auth were
preserved.

## `settings1/` Findings

Files present:

- `musicplayer/settings1/__init__.py`
- `musicplayer/settings1/base.py`
- `musicplayer/settings1/developement.py`
- `musicplayer/settings1/production.py`

Usage findings:

- `manage.py`, `wsgi.py`, and `asgi.py` default to `musicplayer.settings`, not
  `musicplayer.settings1.*`.
- No command imports `musicplayer.settings1.*` by default.
- Existing recovery documentation references `settings1/` as legacy evidence.
- The modules contain no literal secret values, but they read `SECRET_KEY` and
  database credentials from environment variables.
- `developement.py` is misspelled, enables debug-toolbar, and assumes
  PostgreSQL.
- `production.py` contains placeholder `ALLOWED_HOSTS` and an empty PostgreSQL
  port.

Decision: do not delete `settings1/` in this phase. It appears obsolete for the
current runtime, but deletion should wait for the settings-modernization phase so
the project can either remove it with documentation updates or replace it with a
tested settings package.

## Import Audit

| Search target | Confirmed finding | Classification | Action |
| --- | --- | --- | --- |
| `is_safe_url` | Runtime import in `authentication.views` | Safe to replace now | Replaced. |
| `django.conf.urls.url` | None in runtime code | False positive/not used | None. |
| `ugettext`, `ugettext_lazy` | None in runtime code | False positive/not used | None. |
| `force_text`, `smart_text` | None in runtime code | False positive/not used | None. |
| old URL resolver imports | None in runtime code | False positive/not used | None. |
| old middleware imports | None in runtime code | False positive/not used | None. |
| removed model fields/arguments | None in app models | False positive/not used | None. |
| old timezone functions | None in runtime code | False positive/not used | None. |
| deprecated test APIs | None found | False positive/not used | None. |
| `USE_L10N` | Active and legacy settings | Must wait for Django upgrade | Documented. |
| `SOCIALACCOUNT_QUERY_EMAIL` | Active and legacy settings | Must wait for allauth upgrade | Documented. |

## Settings and Middleware Compatibility Audit

- `MIDDLEWARE` uses standard Django middleware compatible with Django 3.0.
- Template context processors include `request`, which allauth needs.
- Authentication backends preserve local auth and allauth integration.
- Installed apps include Django sites and allauth provider apps.
- Static/media settings remain local-development oriented and unchanged.
- No `DEFAULT_AUTO_FIELD` is defined; this is expected on Django 3.0 and should
  be addressed when crossing into Django 3.2+.
- Timezone and language settings remain unchanged.
- Password hashers are default Django hashers; `argon2-cffi` is installed but
  not configured.
- No custom test runner is configured.

## Recommended Staged Runtime Path

Do not perform these steps in this branch.

1. Keep the current Python 3.8.10 and Django 3.0.8 compatibility-prep branch
   passing.
2. Create a new virtual environment on a supported Python version. Proposed
   Python target: Python 3.12, because it is supported by Django 5.2 LTS and has
   mature third-party wheel coverage. Re-check this before implementation.
3. Install an intermediate Django/allauth dependency set. Proposed intermediate
   Django target: Django 3.2 LTS first, then Django 4.2 LTS if needed, because
   these provide smaller compatibility steps than jumping directly from 3.0 to a
   current LTS.
4. Fix warnings and failing tests at each step.
5. Upgrade to the selected supported Django LTS. Proposed final Django target:
   Django 5.2 LTS, pending dependency compatibility confirmation.
6. Modernize django-allauth settings against the selected allauth release.
   Proposed allauth target range: a current 65.x release compatible with the
   selected Django/Python runtime, verified in the upgrade branch.
7. Remove temporary compatibility shims only after the final target no longer
   needs them.
8. Regenerate clean direct dependency constraints and remove unused packages.

## Exact Prerequisites for the Next Upgrade Branch

- Keep this branch's tests and smoke harness passing.
- Choose and document the exact Python, Django, and allauth versions after
  checking current compatibility matrices and release notes.
- Create a clean virtual environment instead of modifying the recovery venv in
  place.
- Preserve the SQLite recovery baseline until database modernization begins.
- Do not combine dependency cleanup, settings hardening, playlist redesign, or
  upload validation with the first runtime upgrade.

## Rollback Notes

Rollback for this phase is straightforward:

- restore `authentication.views` to its previous `is_safe_url` import and helper
  if needed,
- remove `authentication.compat`,
- remove the new compatibility tests,
- remove this document and the roadmap status note.

No migrations, database files, media files, or dependency files are involved.

## Verification Results

- `manage.py check`: passed, no issues.
- `makemigrations --check --dry-run`: passed, no changes detected.
- `manage.py test`: passed, 97 tests.
- `recovery_smoke_test`: passed, 27 checks, overall PASS.
- `git diff --check`: clean.
