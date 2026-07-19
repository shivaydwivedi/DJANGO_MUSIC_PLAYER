# Verification Checklist

## Baseline Commands

Run these before and after each modernization phase:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py recovery_smoke_test
git status --short
git diff --stat
git diff --name-only
git diff --check
```

## Expected Recovery Baseline

- Automated tests: 85.
- Smoke checks: 27.
- `recovery_smoke_test`: overall PASS.

## Data Safety Queries for Future Migration Phases

Before adding database constraints, inspect duplicates with Django shell queries
similar to:

```python
from django.db.models import Count
from musicapp.models import Favourite, Playlist, Recent

Favourite.objects.values("user_id", "song_id").annotate(c=Count("id")).filter(c__gt=1)
Playlist.objects.values("user_id", "playlist_name", "song_id").annotate(c=Count("id")).filter(c__gt=1)
Recent.objects.values("user_id", "song_id").annotate(c=Count("id")).filter(c__gt=1)
```

## Release Gate

A modernization phase is ready for review only when:

- Runtime behavior changes are covered by focused tests.
- Full tests pass.
- Smoke checks pass.
- `makemigrations --check --dry-run` is clean unless the phase explicitly
  includes migrations.
- `git diff --check` is clean.
- The changed-file list matches the approved scope.
