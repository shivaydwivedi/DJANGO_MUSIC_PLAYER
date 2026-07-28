# Repository Cleanup And Independent Rebrand

## Phase 17 Scope

Branch: `modernization/repository-cleanup-rebrand`

This phase cleans the tracked repository and presents Sonica as a standalone
modern Django music application. It does not delete ignored local environments,
local databases, local environment files, uploaded media, or collected static
output.

## Tracked Files Removed

Removed obsolete root-level planning and report files whose useful engineering
history is superseded by the structured documentation in `docs/modernization/`:

- `DATABASE_RECOVERY_REPORT.md`
- `PAGE_SMOKE_TEST_REPORT.md`
- `PROJECT_OVERHAUL_PLAN.md`
- `PROJECT_RECOVERY_CHECKLIST.md`
- `RUNTIME_VERIFICATION_REPORT.md`
- `SYSTEM_RECOVERY_ANALYSIS.md`

Removed old direct-dependency snapshots because `requirements.txt` is the
current supported Python 3.12 / Django 5.2 dependency file:

- `requirements-django32.txt`
- `requirements-django42.txt`

## Files Retained

Retained:

- application code in `authentication/`, `musicapp/`, and `musicplayer/`;
- all migrations;
- active templates and static source assets;
- `media/.gitkeep`;
- `.env.example`;
- `LICENSE`;
- `Procfile`;
- `requirements.txt`;
- `docs/modernization/`, including historical engineering notes that still help
  explain migration, deployment, and schema decisions.

The modernization docs remain intentionally technical. Public presentation now
lives primarily in `README.md` and `ACKNOWLEDGEMENTS.md`.

## Ignored Local Artifacts Not Deleted

The following local artifacts were identified as ignored and intentionally left
on disk:

- `.python38/`
- `.venv/`
- `.venv-clean-install/`
- `.venv-django32/`
- `.venv-django42/`
- `.venv-django52/`
- `.env`
- `db.sqlite3`
- `media/*` except `media/.gitkeep`
- `staticfiles/`

The active runtime environment remains `.venv-django52`.

## Naming Changes

Primary smoke command:

```powershell
.\.venv-django52\Scripts\python.exe manage.py project_smoke_test
```

Compatibility alias:

```powershell
.\.venv-django52\Scripts\python.exe manage.py recovery_smoke_test
```

The alias is retained temporarily for existing local automation. It imports the
same command implementation and keeps output behavior unchanged.

## Attribution Decision

Public attribution is consolidated in `ACKNOWLEDGEMENTS.md`. The README links to
that file, and `LICENSE` preserves the original MIT license notice.

Git history was not rewritten.

## Remaining Cleanup Deferred

Final screenshot capture, architecture diagram polish, GitHub presentation, and
portfolio-facing deployment documentation remain deferred to
`modernization/portfolio-release-polish`.
