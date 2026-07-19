# Dependency Audit

## Direct Requirements

The project currently pins these packages in `requirements.txt`:

| Package | Version | Observed role |
| --- | ---: | --- |
| argon2-cffi | 20.1.0 | Optional password hasher support; not configured in active settings. |
| asgiref | 3.2.10 | Django dependency. |
| certifi | 2020.6.20 | Requests/allauth dependency. |
| cffi | 1.14.0 | argon2 dependency. |
| chardet | 3.0.4 | Requests dependency. |
| defusedxml | 0.6.0 | allauth/OpenID XML hardening dependency. |
| Django | 3.0.8 | Active web framework. |
| django-allauth | 0.42.0 | Installed for account/social login. |
| django-crispy-forms | 1.9.1 | Installed and configured; no active template usage found. |
| django-debug-toolbar | 2.2 | Used only by legacy `settings1/developement.py`. |
| django-environ | 0.4.5 | No active import found; active settings use python-decouple. |
| django-model-utils | 4.0.0 | No active import found. |
| django-redis | 4.12.1 | No active cache configuration found. |
| djangorestframework | 3.11.0 | No active app, import, API route, or serializer usage found. |
| idna | 2.10 | Requests dependency. |
| oauthlib | 3.1.0 | allauth/request-oauth dependency. |
| pycparser | 2.20 | cffi dependency. |
| python-decouple | 3.3 | Active settings loader for `SECRET_KEY`, `DEBUG`, and Google auth flag. |
| python-slugify | 4.0.1 | No active import found. |
| python3-openid | 3.2.0 | allauth dependency. |
| pytz | 2020.1 | Django 3 era timezone dependency. |
| requests | 2.24.0 | allauth/request-oauth dependency. |
| requests-oauthlib | 1.3.0 | social auth dependency. |
| six | 1.15.0 | Compatibility dependency. |
| sqlparse | 0.3.1 | Django dependency. |
| text-unidecode | 1.3 | python-slugify dependency. |
| urllib3 | 1.25.9 | Requests dependency. |

The installed environment also contains `redis==6.1.1` and
`async-timeout==5.0.1`, which appear to be resolved dependencies of
`django-redis` rather than direct project code requirements.

## Likely Unused or Replaceable Dependencies

- `django-crispy-forms`: configured but no `{% crispy %}` usage or crispy helper
  usage was found in the active app.
- `django-debug-toolbar`: only referenced in the legacy misspelled
  `settings1/developement.py` module.
- `django-environ`: present but active settings use `python-decouple`.
- `django-model-utils`: no imports found.
- `django-redis`: no active cache backend configuration found.
- `djangorestframework`: no REST app, serializer, viewset, or API URL usage found.
- `python-slugify` and `text-unidecode`: no slug field or active import found.
- `argon2-cffi`: not harmful, but `PASSWORD_HASHERS` does not opt into Argon2.

These should be removed only in a dedicated dependency cleanup phase after a
fresh install test confirms the app still boots and all tests pass.

## Frontend Vendor Dependencies

`templates/base.html` currently loads CDN-hosted Bootstrap 4.0.0, jQuery slim
3.2.1, Popper 1.12.9, Font Awesome 4.7.0, Smooth Scroll 16.1.3, and Google
Fonts. Local static bundles for `amplitude.min.js` and `wavesurfer.min.js`
exist, but no active template include was found.

## Deprecated or Upgrade-Sensitive APIs

- `authentication.views` imports and calls `is_safe_url`; use
  `url_has_allowed_host_and_scheme` before upgrading Django.
- `USE_L10N` is present in active and legacy settings; remove it before a modern
  Django upgrade.
- `SOCIALACCOUNT_QUERY_EMAIL` is an old allauth setting and should be checked
  against the target allauth release.
- `pytz` is normal for Django 3.0 but should be revisited for modern Django's
  `zoneinfo` direction.

## Dependency Strategy

1. Add a clean install verification step before removing anything.
2. Separate runtime dependencies from transitive pins.
3. Remove unused dependencies in a small phase.
4. Upgrade Django-adjacent dependencies before upgrading Django itself.
5. Add a lockfile or repeatable resolver process once the target runtime is
   chosen.
