# Production Security Hardening

## Baseline Deployment Warnings

Before changes, a production-like `manage.py check --deploy` with a temporary
secret and `example.com` host reported:

- `security.W004`: `SECURE_HSTS_SECONDS` was not set.
- `security.W008`: `SECURE_SSL_REDIRECT` was not true.
- `security.W009`: the temporary test `SECRET_KEY` was too weak.
- `security.W012`: `SESSION_COOKIE_SECURE` was not true.
- `security.W016`: `CSRF_COOKIE_SECURE` was not true.

Classification:

- must fix now: strong-secret validation, secure-cookie support;
- intentionally configurable: SSL redirect, because a trusted load balancer may
  handle redirects;
- deferred/deployment-specific: HSTS rollout duration and preload;
- false positives: none.

No deployment checks were silenced.

## Security Settings Added

Environment-driven settings now include:

- `SECURE_SSL_REDIRECT`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `SECURE_HSTS_SECONDS`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `SECURE_HSTS_PRELOAD`
- `SECURE_CONTENT_TYPE_NOSNIFF`
- `SECURE_REFERRER_POLICY`
- `X_FRAME_OPTIONS`
- `SESSION_COOKIE_HTTPONLY`
- `SESSION_COOKIE_SAMESITE`
- `CSRF_COOKIE_SAMESITE`
- `TRUST_X_FORWARDED_PROTO`
- `USE_X_FORWARDED_HOST`

## Defaults and Rationale

Local development remains easy:

- `DEBUG=True`
- `SECURE_SSL_REDIRECT=False`
- `SESSION_COOKIE_SECURE=False`
- `CSRF_COOKIE_SECURE=False`
- `SECURE_HSTS_SECONDS=0`
- proxy-header trust disabled

Production-like `DEBUG=False` defaults:

- session and CSRF cookies default to secure;
- HSTS remains disabled until HTTPS deployment is verified;
- SSL redirect remains configurable rather than forced;
- content-type sniffing protection is enabled;
- referrer policy defaults to `strict-origin-when-cross-origin`;
- clickjacking protection defaults to `DENY`.

## Environment Contract

See `.env.example` for the full contract. `ALLOWED_HOSTS` and
`CSRF_TRUSTED_ORIGINS` use comma-separated values. CSRF origins must be absolute
URLs, and production origins must use `https://`.

`SECRET_KEY` must be supplied for production. Generate one locally with Django's
`get_random_secret_key` helper and store it only in the real environment, not in
repository files.

## Proxy Header Trust

`SECURE_PROXY_SSL_HEADER` is not set by default.

Only when `TRUST_X_FORWARDED_PROTO=True`, Sonica sets:

```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

Use this only behind a trusted proxy that strips incoming
`X-Forwarded-Proto` and sets it correctly. Local development does not trust this
header. `USE_X_FORWARDED_HOST` defaults to false.

## HSTS Guidance

HSTS defaults to disabled with `SECURE_HSTS_SECONDS=0`.

Validation prevents enabling `SECURE_HSTS_INCLUDE_SUBDOMAINS` or
`SECURE_HSTS_PRELOAD` while HSTS seconds is zero. Start with a short HSTS
duration only after HTTPS is verified, then increase deliberately.

## Cookie Security

For `DEBUG=False`, secure session and CSRF cookies default to true. They remain
environment-configurable for platform rehearsals, but production HTTPS
deployments should keep both enabled.

## Static and Media Readiness

`STATIC_ROOT` is defined as `staticfiles`, separate from source static files in
`static/`, so `collectstatic` has a clear output target. Local static loading is
preserved.

Uploaded media still uses local `media/`. Django should not serve production
uploaded media directly; object storage or platform media handling is deferred.

## Error Pages

Simple branded `400.html`, `403.html`, `404.html`, and `500.html` templates were
added. Tests confirm `DEBUG=False` 404/500 responses do not expose traceback
details, exception text, or the configured secret.

## Logging Decision

A minimal console logging configuration was added for Django warnings and
request errors. It avoids verbose SQL logging, request-body logging, and
external monitoring services.

## Final Deployment Check

A valid production-like deployment check should set:

- `DEBUG=False`
- a long temporary `SECRET_KEY`
- `ALLOWED_HOSTS=example.com`
- `CSRF_TRUSTED_ORIGINS=https://example.com`
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- deliberate HSTS values

The final check passed with no deployment warnings under that controlled
configuration.

## Tests Added

Settings tests now cover:

- secure production defaults;
- local development defaults;
- SSL redirect parsing;
- secure session and CSRF cookie parsing;
- HSTS seconds parsing and invalid combinations;
- explicit proxy-header opt-in and disabled default;
- production rejection of fallback, short, and low-quality secrets;
- production rejection of wildcard `ALLOWED_HOSTS`;
- production rejection of non-HTTPS CSRF origins;
- static root separation;
- successful `check --deploy` under valid production-like settings;
- `DEBUG=False` 404 and 500 response safety.

## Remaining Deployment Risks

- No hosting platform is selected.
- No PostgreSQL, Redis, Docker, CI, or external monitoring is configured.
- Uploaded media storage remains local-only.
- HSTS duration and preload require real HTTPS deployment validation.
- Reverse-proxy trust must be enabled only for a known trusted proxy.

## Rollback Instructions

1. Revert the production security settings in `musicplayer/settings.py`.
2. Revert `.env.example`, README, roadmap, and settings-cleanup documentation
   updates.
3. Remove the simple error templates if reverting the production response
   polish.

No models or migrations are involved.

## Exact Next Branch

`modernization/deployment-readiness`

## Exact Next Task

Create a platform-neutral deployment readiness plan for database, static files,
uploaded media, and environment management without choosing a hosting provider.

Update: this follow-up was completed on `modernization/deployment-readiness`.
