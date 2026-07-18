# Galvanic Music Player

Galvanic is a recovered and redesigned Django music-player application. It keeps the original project idea, browser-based music discovery and playback, while adding a safer backend baseline, automated regression coverage, and a modern dark interface suitable for portfolio presentation.

The current release is the frontend QA pass that follows the `recovery-v1` tag. It is designed for local demonstration with legal, user-supplied media.

## Recovery Story

This project began as an inherited Django codebase that could not be run reliably in a modern local environment. The recovery work rebuilt the runtime around Django 3.0.8 and Python 3.8.10, restored database migrations, removed assumptions about archived media, repaired empty-library and missing-media crashes, and added focused tests around favourites, playlists, recent history, protected pages, and smoke coverage.

The frontend work then introduced a shared design system, responsive page layouts, reusable song cards, protected-page polish, redesigned authentication screens, and consistent empty and missing-media states.

## Features

- Public song browsing across home, all songs, Hindi songs, and English songs.
- Search and filter controls for catalog pages.
- Song detail pages with guarded cover and audio rendering.
- Authenticated favourites.
- Authenticated playlists scoped to the current user.
- Authenticated recent-listening history.
- Fixed browser audio player shell.
- Empty-library and missing-media fallbacks.
- Responsive dark UI with keyboard-visible focus states.
- Recovery smoke command covering the main app routes.

## Screenshots

No screenshot files are committed with this repository. For a portfolio README or project page, capture fresh screenshots from local demo data and store only authorized images.

Recommended captures:

| View | Suggested filename |
| --- | --- |
| Anonymous desktop home | `docs/screenshots/home-anonymous-desktop.png` |
| Authenticated desktop home | `docs/screenshots/home-authenticated-desktop.png` |
| Mobile home with collapsed navigation | `docs/screenshots/home-mobile.png` |
| Expanded mobile navigation | `docs/screenshots/mobile-navigation-expanded.png` |
| Song detail and player | `docs/screenshots/song-detail-player.png` |
| Empty library state | `docs/screenshots/empty-library.png` |
| Missing cover fallback | `docs/screenshots/missing-cover-card.png` |

## Stack

- Python 3.8.10
- Django 3.0.8
- SQLite for local development
- Bootstrap 4
- Font Awesome 4
- CSS custom properties for the design-token layer

## Local Setup

Create and activate a Python 3.8 virtual environment, then install dependencies:

```powershell
py -3.8 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Update `.env` for your machine:

```env
SECRET_KEY=replace-with-a-long-random-secret-key
DEBUG=True
```

Apply migrations and create an admin user:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Run the development server:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Demo Data And Media

The original music library is not included. Add demo songs through Django admin using original, openly licensed, or otherwise authorized audio and cover art.

Do not commit `db.sqlite3`, uploaded media, secrets, or copyrighted assets. The application includes fallbacks for recovered rows that have missing cover or audio fields.

## Verification

Run Django checks:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Run the automated tests:

```powershell
.\.venv\Scripts\python.exe manage.py test
```

Run the recovery smoke harness:

```powershell
.\.venv\Scripts\python.exe manage.py recovery_smoke_test
```

Expected recovery baseline:

- 64 automated tests passing.
- 27 smoke checks passing.
- Smoke result reports overall `PASS`.

## Project Structure

```text
authentication/          User signup, login, and logout views
musicapp/                Songs, playback, favourites, playlists, recent history, tests
templates/               Shared layout and page templates
static/musicapp/css/     Frontend design system and page styles
media/                   Local uploaded media, not committed
recovery_smoke_report.*  Local smoke output, not committed
```

## Security And Recovery Improvements

- Server-side login protection for user-owned pages and mutations.
- POST-only mutations for favourites and playlists.
- Current-user ownership isolation for favourites, playlists, and recent history.
- Safer request validation for missing and invalid IDs.
- Duplicate handling for favourite and playlist operations.
- Missing media guards before accessing file URLs.
- Empty-library page rendering without database side effects.
- Regression tests for repaired recovery paths.

## Current Limitations

- This is a Django 3.0.8 recovery baseline, not a dependency modernization branch.
- The playlist model stores playlist membership rows. A truly empty named playlist cannot exist under that model; when the final song is removed, no row remains and the playlist route returns 404.
- Uploaded media and the local SQLite database are intentionally excluded from version control.
- Production deployment hardening is outside this release QA branch.

## Roadmap

- Modernize Django and Python after the recovery baseline is preserved.
- Introduce a dedicated playlist container model in a future model-redesign phase.
- Add curated demo fixtures using original or openly licensed media.
- Add deployment configuration and production storage.
- Expand visual regression coverage for the redesigned interface.

## License And Attribution

Original work:

Copyright (c) 2020 rajaprerak

Recovery, redesign, and subsequent modifications:

Copyright (c) 2026 Shivay Dwivedi

See `LICENSE` for the full MIT License terms.
