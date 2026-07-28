# Dependency Cleanup

## Canonical Requirements Decision

`requirements.txt` is now the canonical supported runtime dependency file.

Canonical installation command:

```powershell
.\.venv-django52\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` is the only retained runtime dependency file. The older
Django 3.2 and Django 4.2 snapshots were removed during repository cleanup
because this document records the staged upgrade history.

## Supported Runtime

- Python: 3.12.
- Django: 5.2.16.
- Dependency file: `requirements.txt`.

## Direct Dependency Table

| Dependency | Imported directly? | Configured? | Used in templates? | Required at runtime? | Decision |
| --- | --- | --- | --- | --- | --- |
| `Django==5.2.16` | Yes | Yes | Yes, template engine | Yes | Retain direct pin. |
| `django-allauth[socialaccount]==65.18.0` | Yes | Yes | Yes, `socialaccount` tags | Yes | Retain direct pin with socialaccount extra. |
| `python-decouple==3.8` | Yes, in settings | Yes | No | Yes | Retain direct pin. |
| `django-crispy-forms` | No | Previously only | No | No | Removed. |
| `Pillow` | No | No | No | No | Removed. |
| `requests-oauthlib` | No | No | No | No | Removed direct dependency. |
| `python3-openid` | No | No | No | No | Removed direct dependency. |
| `PyJWT` | No | Via allauth extra | No | Yes, Google provider import path | Provided transitively by `django-allauth[socialaccount]`. |
| `cryptography` | No | Via allauth extra | No | Yes, Google provider JWT helper | Provided transitively by `django-allauth[socialaccount]`. |

## Removed Dependencies

Removed from the canonical direct dependency file:

- `argon2-cffi`
- `asgiref`
- `certifi`
- `cffi`
- `chardet`
- `defusedxml`
- `django-crispy-forms`
- `django-debug-toolbar`
- `django-environ`
- `django-model-utils`
- `django-redis`
- `djangorestframework`
- `idna`
- `oauthlib`
- `Pillow`
- `pycparser`
- `python-slugify`
- `python3-openid`
- `pytz`
- `requests`
- `requests-oauthlib`
- `six`
- `sqlparse`
- `text-unidecode`
- `urllib3`

Several remain installed transitively in environments because Django/allauth
need them, but they are no longer direct Sonica requirements.

## Crispy Forms Decision

`django-crispy-forms` was removed.

Evidence:

- no `{% load crispy_forms_tags %}` usage;
- no `|crispy` filters;
- no `FormHelper` or crispy layout imports;
- no form template uses crispy rendering;
- the only active references were `crispy_forms` in `INSTALLED_APPS` and
  `CRISPY_TEMPLATE_PACK`.

Removed active settings:

- `crispy_forms` from `INSTALLED_APPS`;
- `CRISPY_TEMPLATE_PACK`.

Authentication form rendering is covered by the existing login/signup/profile
tests and by both supported and clean-install full test runs.

## Allauth Provider Dependency Decision

`django-allauth` metadata for the selected version declares a `socialaccount`
extra. That extra installs the provider stack needed by the configured Google
social provider, including:

- `requests`
- `oauthlib`
- `PyJWT`
- `cryptography`

Therefore:

- `requests-oauthlib` is not retained directly;
- `python3-openid` is not retained directly;
- `PyJWT` is provided through the allauth socialaccount extra;
- `cryptography` is provided through the allauth socialaccount extra.

Google provider import probes passed in both the supported and clean-install
environments.

## Historical Requirements Files

- `requirements.txt`: canonical supported runtime file.
- Django 3.2 and Django 4.2 direct-dependency snapshots: removed during
  repository cleanup because `requirements.txt` is authoritative and the staged
  upgrade history is documented here.
- `requirements-django52.txt`: removed because `requirements.txt` now owns the
  final Django 5.2 runtime.

## Clean Install Procedure

Created ignored disposable environment:

```powershell
py -3.12 -m venv .venv-clean-install
.\.venv-clean-install\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv-clean-install\Scripts\python.exe -m pip install -r requirements.txt
```

`.venv-clean-install/` was added to `.gitignore`.

## Clean Install Verification

- `pip check`: passed.
- `python -m django --version`: 5.2.16.
- `manage.py check`: passed.
- `makemigrations --check --dry-run`: no changes detected.
- `manage.py test`: 97 tests passed.
- `project_smoke_test`: 27 checks passed, overall PASS.
- Import probe: Django, allauth, Google provider, python-decouple, project URLs,
  and management command discovery passed.

## Dependency Graph Notes

Canonical direct dependencies:

- `Django==5.2.16`
- `django-allauth[socialaccount]==65.18.0`
- `python-decouple==3.8`

Important transitives currently resolved by clean install:

- `asgiref`
- `certifi`
- `cffi`
- `charset-normalizer`
- `cryptography`
- `idna`
- `oauthlib`
- `pycparser`
- `PyJWT`
- `requests`
- `sqlparse`
- `tzdata`
- `urllib3`

No vulnerability audit tool was run, so this report does not claim that the
dependency set has no vulnerabilities. A security audit remains a separate
future task.

## Remaining Dependency Risks

- Transitive versions are resolved by pip from package metadata rather than
  locked in a full lockfile.
- Legacy `settings1/` cleanup is handled by the follow-up settings cleanup
  phase.
- Social auth remains installed even though Google UI is hidden until explicitly
  configured.
- No dependency vulnerability scan has been performed.

## Rollback Instructions

1. Restore the previous `requirements.txt` from Git if the earlier local
   dependency set is needed.
2. Reinstall `django-crispy-forms` and restore `crispy_forms` settings only if a
   future template actually uses crispy rendering.
3. Recreate `.venv-django52` from the previous dependency file if rolling back
   this cleanup.
4. Remove this report and revert README/roadmap updates.

## Follow-Up

The next branch from this cleanup was `modernization/settings-cleanup`.
