# Logging and Monitoring Audit

## Current State

The project does not define a custom `LOGGING` setting. Runtime visibility comes
from Django defaults, local command output, test failures, user-facing messages,
and the project smoke command.

## Logging Gaps

- No structured application logs.
- No production log level configuration.
- No security/authentication event logging.
- No upload/media validation logging.
- No external error reporting integration.
- No request id or correlation id strategy.
- No health-check endpoint.
- No deployment/runtime metrics.

## Existing Useful Signals

- `manage.py check` validates basic Django configuration.
- Automated tests cover the covered behavior.
- `project_smoke_test` validates important routes and row-count invariants.
- User-facing messages are used for profile, favourite, and playlist outcomes.

## Recommendations

1. Add a small environment-driven `LOGGING` config before production deployment.
2. Log invalid mutation attempts at info/warning level without exposing secrets.
3. Add media upload validation logs only when upload validation exists.
4. Add a health check only when the deployment target needs it.
5. Keep smoke checks as a release gate.
