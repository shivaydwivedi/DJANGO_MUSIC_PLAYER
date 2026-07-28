# Sonica Music Player

Sonica Music Player is a modern Django application for browsing songs, playing music, managing favourites, organizing playlists, and reviewing listening history. It pairs a responsive dark interface with secure authentication, tested POST-only mutation flows, SQLite local development, PostgreSQL deployment support, WhiteNoise static serving, and a Waitress production start path.

## Features

- Public song browsing across home, all songs, Hindi songs, English songs, and recent pages.
- Search and filter controls for catalog views.
- Song detail pages with guarded cover and audio rendering.
- Browser audio player shell.
- Username/password signup, login, logout, and profile pages.
- Optional Google authentication when a real Django Allauth SocialApp is configured.
- Authenticated favourites.
- Authenticated playlist containers and playlist-song membership.
- Authenticated listening-history recording.
- POST-only mutation routes for favourites, playlists, and playback history.
- Empty-library and missing-media fallbacks.
- Health and readiness probes.
- PostgreSQL-ready deployment configuration.
- Responsive dark UI with keyboard-visible focus states.

## Technology Stack

- Python 3.12
- Django 5.2 LTS
- SQLite for local development
- PostgreSQL via `DATABASE_URL` for production deployment
- Django Allauth
- WhiteNoise for production static files
- Waitress WSGI server
- Bootstrap 4
- Font Awesome 4
- CSS custom properties for the design-token layer

## Screenshots

No screenshot files are committed with this repository. For a portfolio README or project page, capture fresh screenshots from local demo data and store only authorized images.

Recommended captures:

| View                                  | Suggested filename                                |
| ------------------------------------- | ------------------------------------------------- |
| Anonymous desktop home                | `docs/screenshots/home-anonymous-desktop.png`     |
| Authenticated desktop home            | `docs/screenshots/home-authenticated-desktop.png` |
| Mobile home with collapsed navigation | `docs/screenshots/home-mobile.png`                |
| Expanded mobile navigation            | `docs/screenshots/mobile-navigation-expanded.png` |
| Song detail and player                | `docs/screenshots/song-detail-player.png`         |
| Empty library state                   | `docs/screenshots/empty-library.png`              |
| Missing cover fallback                | `docs/screenshots/missing-cover-card.png`         |

## Architecture Overview

```text
Browser
  -> Django templates and static assets
  -> Django views and forms
  -> Auth, song, playlist, favourite, and history models
  -> SQLite locally or PostgreSQL in production
```

Operational endpoints:

- `/health/` confirms the application process responds.
- `/ready/` confirms database connectivity with a non-mutating query.

Production serving:

- Waitress runs `musicplayer.wsgi:application`.
- WhiteNoise serves collected static files.
- Uploaded media requires durable platform storage such as a persistent disk or object storage.

## Local Setup

Create and activate a Python 3.12 virtual environment, then install dependencies:

```powershell
py -3.12 -m venv .venv-django52
.\.venv-django52\Scripts\python.exe -m pip install -r requirements.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Update `.env` for your machine:

```env
SECRET_KEY=replace-with-a-long-random-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
CSRF_TRUSTED_ORIGINS=
DATABASE_URL=
ENABLE_GOOGLE_AUTH=False
```

Apply migrations and create an admin user:

```powershell
.\.venv-django52\Scripts\python.exe manage.py migrate
.\.venv-django52\Scripts\python.exe manage.py createsuperuser
```

Run the development server:

```powershell
.\.venv-django52\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Environment Configuration

The supported settings module is `musicplayer.settings`.

Important environment variables:

| Variable                       | Purpose                                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------------------------- |
| `SECRET_KEY`                   | Required for signed cookies and security-sensitive Django features. Use a long production secret. |
| `DEBUG`                        | Use `True` locally and `False` in production.                                                     |
| `ALLOWED_HOSTS`                | Comma-separated hostnames allowed by Django. Required when `DEBUG=False`.                         |
| `CSRF_TRUSTED_ORIGINS`         | Comma-separated absolute trusted origins such as `https://sonica.example.com`.                    |
| `DATABASE_URL`                 | Blank for local SQLite; set to a PostgreSQL URL in production.                                    |
| `DATABASE_CONN_MAX_AGE`        | Persistent database connection lifetime in seconds.                                               |
| `DATABASE_SSL_REQUIRE`         | Set `True` when the PostgreSQL provider requires SSL.                                             |
| `PORT`                         | Platform-provided port for the Procfile start command.                                            |
| `SECURE_SSL_REDIRECT`          | Redirect HTTP to HTTPS when Django is responsible for the redirect.                               |
| `SESSION_COOKIE_SECURE`        | Send session cookies only over HTTPS.                                                             |
| `CSRF_COOKIE_SECURE`           | Send CSRF cookies only over HTTPS.                                                                |
| `SECURE_HSTS_SECONDS`          | Enable HSTS only after HTTPS is verified.                                                         |
| `TRUST_X_FORWARDED_PROTO`      | Trust proxy HTTPS headers only behind a trusted reverse proxy.                                    |
| `ENABLE_GOOGLE_AUTH`           | Shows Google auth UI only when a real SocialApp is configured.                                    |
| `SONICA_MAX_AUDIO_UPLOAD_SIZE` | Maximum uploaded audio size in bytes.                                                             |
| `SONICA_MAX_COVER_UPLOAD_SIZE` | Maximum uploaded cover size in bytes.                                                             |

Never commit `.env`, database files, uploaded media, OAuth credentials, or real production database URLs.

## Database Behavior

When `DATABASE_URL` is blank, Sonica uses local SQLite at `db.sqlite3`. This keeps local setup simple and avoids requiring PostgreSQL for development or tests.

When `DATABASE_URL` is set, Sonica parses it with `dj-database-url`. PostgreSQL URLs select Django's PostgreSQL backend through `psycopg` 3. `DATABASE_SSL_REQUIRE=True` enables provider-required SSL mode, and `DATABASE_CONN_MAX_AGE` controls persistent connection lifetime.

Applying migrations creates or updates schema. It does not transfer local SQLite rows into PostgreSQL. Plan any data migration separately using backups and a disposable rehearsal database.

## Demo Data And Media

The repository does not include a music library. Add demo songs through Django admin using original, openly licensed, or otherwise authorized audio and cover art.

For a repeatable local demo catalog, run:

```powershell
.\.venv-django52\Scripts\python.exe manage.py seed_demo_catalog
```

This creates eight fictional Sonica demo songs with Hindi and English metadata. It does not create users, download files, assign media paths, or add copyrighted songs. Running it repeatedly is safe and does not duplicate rows. Run it once after deployment; do not add it to every build or application startup.



Media remains unavailable until legal persistent media storage is configured.
Local commercial media and `db.sqlite3` must never be deployed.

## Verification

Run Django checks:

```powershell
.\.venv-django52\Scripts\python.exe manage.py check
.\.venv-django52\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Run tests:

```powershell
.\.venv-django52\Scripts\python.exe manage.py test
.\.venv-django52\Scripts\python.exe manage.py test musicapp
```

Run the project smoke harness:

```powershell
.\.venv-django52\Scripts\python.exe manage.py project_smoke_test
```

The older `recovery_smoke_test` command remains as a temporary compatibility alias for existing local automation.

## Deployment Readiness

Collect static files:

```powershell
.\.venv-django52\Scripts\python.exe manage.py collectstatic --noinput
```

Run deployment checks with safe production environment values:

```powershell
.\.venv-django52\Scripts\python.exe manage.py check --deploy
.\.venv-django52\Scripts\python.exe manage.py deployment_readiness_check
```

Production start command:

```text
web: bash scripts/render-start.sh
```

Render deployment details are documented in [docs/deployment/RENDER_DEPLOYMENT.md](docs/deployment/RENDER_DEPLOYMENT.md). PostgreSQL deployment design notes are documented in [docs/modernization/25_POSTGRESQL_DEPLOYMENT.md](docs/modernization/25_POSTGRESQL_DEPLOYMENT.md).

## Project Structure

```text
authentication/       Signup, login, logout, profile, and auth forms
musicapp/             Song browsing, playback, favourites, playlists, history, tests
musicplayer/          Project settings, URLs, WSGI/ASGI, health, readiness
templates/            Shared layout and page templates
static/               Source CSS, fonts, JavaScript, and images
media/                Local uploaded media placeholder; runtime uploads ignored
docs/                 Engineering and deployment documentation
```

## Acknowledgements

See [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md) for project attribution.

## License

Sonica Music Player is distributed under the MIT License. See [LICENSE](LICENSE) for the full license terms.
