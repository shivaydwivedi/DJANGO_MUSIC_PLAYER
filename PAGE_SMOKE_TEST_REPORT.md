# Page Smoke Test Report

## 1. Executive Result

Empty-database page smoke testing confirmed multiple page-level blockers.

The Django development server was started successfully on:

```text
http://127.0.0.1:8000/
```

A live HTTP request to:

```text
http://127.0.0.1:8000/authentication/login/
```

returned HTTP 200.

Most core public music-library pages do not render with an empty `musicapp_song` table. The first confirmed page-rendering blocker is:

```text
GET /
musicapp.models.Song.DoesNotExist: Song matching query does not exist.
musicapp/views.py:36
last_played_song = Song.objects.get(id=7)
```

No source files were modified. No users, songs, playlists, favourites, recent-history rows, seed data, archived database content, or archived media were created. Database row counts stayed unchanged.

## 2. Repository and Database State

Repository checks:

| Check | Result |
| --- | --- |
| Active branch | `recovery/runtime-verification` |
| `git status --short` before testing | no output |
| `db.sqlite3` ignore rule | `.gitignore:3:db.sqlite3	db.sqlite3` |
| `db.sqlite3` size | `266240` bytes |
| Django system check | `System check identified no issues (0 silenced).` |
| Migrations | all expected migrations applied |

Database row counts before route requests:

```json
{"auth_user": 0, "musicapp_favourite": 0, "musicapp_playlist": 0, "musicapp_recent": 0, "musicapp_song": 0}
```

The active `media/` directory was not populated, and no archived media was restored.

## 3. Route Inventory

Routes were inspected from `musicplayer/urls.py`, `musicapp/urls.py`, and `authentication/urls.py`.

| Path | Name | View | Expected method | Auth requirement | Expected template | Requires object ID |
| --- | --- | --- | --- | --- | --- | --- |
| `/` | `index` | `musicapp.views.index` | GET | Public | `musicapp/index.html` | No |
| `/<int:song_id>/` | `detail` | `musicapp.views.detail` | GET/POST | Login required | `musicapp/detail.html` | Yes, Song ID |
| `/mymusic/` | `mymusic` | `musicapp.views.mymusic` | GET | Public in URL | `musicapp/mymusic.html` | No |
| `/playlist/` | `playlist` | `musicapp.views.playlist` | GET | Not decorated | `musicapp/playlist.html` | No |
| `/playlist/<str:playlist_name>/` | `playlist_songs` | `musicapp.views.playlist_songs` | GET/POST | Not decorated | `musicapp/playlist_songs.html` | Playlist name |
| `/favourite/` | `favourite` | `musicapp.views.favourite` | GET/POST | Not decorated | `musicapp/favourite.html` | No |
| `/all_songs/` | `all_songs` | `musicapp.views.all_songs` | GET | Public | `musicapp/all_songs.html` | No |
| `/recent/` | `recent` | `musicapp.views.recent` | GET | Not decorated | `musicapp/recent.html` | No |
| `/hindi_songs/` | `hindi_songs` | `musicapp.views.hindi_songs` | GET | Public | `musicapp/hindi_songs.html` | No |
| `/english_songs/` | `english_songs` | `musicapp.views.english_songs` | GET | Public | `musicapp/english_songs.html` | No |
| `/play/<int:song_id>/` | `play_song` | `musicapp.views.play_song` | GET | Login required | redirect | Yes, Song ID |
| `/play_song/<int:song_id>/` | `play_song_index` | `musicapp.views.play_song_index` | GET | Login required | redirect | Yes, Song ID |
| `/play_recent_song/<int:song_id>/` | `play_recent_song` | `musicapp.views.play_recent_song` | GET | Login required | redirect | Yes, Song ID |
| `/authentication/login/` | `login` | `authentication.views.login_request` | GET/POST | Public | `authentication/login.html` | No |
| `/authentication/signup/` | `signup` | `authentication.views.signup_request` | GET/POST | Public | `authentication/signup.html` | No |
| `/authentication/logout/` | `logout` | `authentication.views.logout_request` | GET | Public | redirect | No |
| `/accounts/` routes | allauth names | `allauth.urls` | varies | Public/auth-dependent | allauth templates | No |
| `/admin/` | admin index | `django.contrib.admin.site.urls` | GET | Staff login required | admin login redirect | No |

## 4. Server Startup Result

Several PowerShell launch methods were attempted. `Start-Process` failed before Django startup because the shell environment contains duplicate `Path`/`PATH` keys:

```text
Start-Process : Item has already been added. Key in dictionary: 'Path'  Key being added: 'PATH'
```

A short foreground probe of `runserver --noreload` timed out without flushed output.

The server was then started successfully with Python `subprocess.Popen`:

```text
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

Evidence:

```text
Listening port: 127.0.0.1:8000
Live request: GET /authentication/login/
HTTP status: 200
Response length: 7573
```

Server log excerpt:

```text
[18/Jul/2026 19:27:35] "GET /authentication/login/ HTTP/1.1" 200 7573
```

The server was stopped after testing. Final port check showed no process listening on `:8000`.

Selected settings module:

```text
musicplayer.settings
```

No startup exception was observed in the successful server launch path.

## 5. Public Route Results

Requests were made with Django's test client without following redirects. This was used after the server-start process issues so view/template exceptions could be captured route by route without creating permanent test files.

| URL | Method | Result | Status/redirect | Exception | Evidence | Primary category | Severity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | GET | Server error | 500-equivalent exception | `DoesNotExist: Song matching query does not exist.` | `musicapp/views.py:36`, `Song.objects.get(id=7)` | Empty-library defect | Critical |
| `/all_songs/` | GET | Server error | 500-equivalent exception | `DoesNotExist: Song matching query does not exist.` | `musicapp/views.py:166`, `Song.objects.get(id=7)` | Empty-library defect | Critical |
| `/hindi_songs/` | GET | Server error | 500-equivalent exception | `DoesNotExist: Song matching query does not exist.` | `musicapp/views.py:84`, `Song.objects.get(id=7)` | Empty-library defect | Critical |
| `/english_songs/` | GET | Server error | 500-equivalent exception | `DoesNotExist: Song matching query does not exist.` | `musicapp/views.py:107`, `Song.objects.get(id=7)` | Empty-library defect | Critical |
| `/recent/` | GET | Server error | 500-equivalent exception | `DoesNotExist: Song matching query does not exist.` | `musicapp/views.py:209`, `Song.objects.get(id=7)` | Empty-library defect | Critical |
| `/favourite/` | GET | Server error | 500-equivalent exception | `TypeError: 'AnonymousUser' object is not iterable` | `musicapp/views.py:307`, filter uses `request.user` without login requirement | Authorization defect | High |
| `/playlist/` | GET | Server error | 500-equivalent exception | `TypeError: 'AnonymousUser' object is not iterable` | `musicapp/views.py:287`, filter uses `request.user` without login requirement | Authorization defect | High |
| `/playlist/test-list/` | GET | Server error | 500-equivalent exception | `TypeError: 'AnonymousUser' object is not iterable` | `musicapp/views.py:293`, filter uses `request.user` without login requirement | Authorization defect | High |
| `/mymusic/` | GET | Pass | 200 | none | rendered `musicapp/mymusic.html`, `base.html` | Working behavior | Low |

## 6. Authentication Route Results

| URL | Method | Result | Status/redirect | Templates | Primary category |
| --- | --- | --- | --- | --- | --- |
| `/authentication/login/` | GET | Pass | 200 | `authentication/login.html`, `base.html`, crispy Bootstrap templates | Working behavior |
| `/authentication/signup/` | GET | Pass | 200 | `authentication/signup.html`, `base.html`, crispy Bootstrap templates | Working behavior |
| `/authentication/logout/` | GET | Redirect expected | 302 to `/` | none | Expected redirect |
| `/accounts/login/` | GET | Pass | 200 | `account/login.html`, `account/base.html`, `base.html` | Working behavior |

Notes:

- The custom login and signup pages render with zero users.
- The allauth login page renders with zero users.
- Logout redirects to `/`; the target was not followed because `/` is known to fail on empty database.

## 7. Admin Route Result

| URL | Method | Result | Status/redirect | Primary category |
| --- | --- | --- | --- | --- |
| `/admin/` | GET | Redirect expected | 302 to `/admin/login/?next=/admin/` | Expected redirect |

Django admin is structurally reachable and correctly redirects anonymous users to the admin login page.

## 8. Invalid Object-ID Results

Representative invalid IDs were tested with no songs in the database.

| URL | Method | Result | Status/redirect | Mutation observed | Notes |
| --- | --- | --- | --- | --- | --- |
| `/1/` | GET | Redirect expected | 302 to `/authentication/login/?next=/1/` | No | `detail` is protected by `login_required`; invalid Song lookup was not reached anonymously. |
| `/play/1/` | GET | Redirect expected | 302 to `/authentication/login/?next=/play/1/` | No | `play_song` is protected by `login_required`; history mutation was not reached anonymously. |
| `/play_song/1/` | GET | Redirect expected | 302 to `/authentication/login/?next=/play_song/1/` | No | `play_song_index` is protected by `login_required`; history mutation was not reached anonymously. |
| `/play_recent_song/1/` | GET | Redirect expected | 302 to `/authentication/login/?next=/play_recent_song/1/` | No | `play_recent_song` is protected by `login_required`; history mutation was not reached anonymously. |

The invalid-object behavior for authenticated users was not tested because the task prohibits creating users.

## 9. Database State Before and After

Before requests:

```json
{"auth_user": 0, "musicapp_favourite": 0, "musicapp_playlist": 0, "musicapp_recent": 0, "musicapp_song": 0}
```

After requests:

```json
{"auth_user": 0, "musicapp_favourite": 0, "musicapp_playlist": 0, "musicapp_recent": 0, "musicapp_song": 0}
```

Confirmed:

- No Song rows were added.
- No User rows were added.
- No Playlist rows were added.
- No Favourite rows were added.
- No Recent rows were added.
- No GET request mutated the database in this anonymous smoke test.

## 10. Confirmed Failures

### Finding 1

* **Finding:** Homepage crashes with an empty song library.
* **Status:** Confirmed
* **Route:** `/`
* **HTTP method:** GET
* **HTTP result:** Server error, 500-equivalent exception
* **Exception:** `musicapp.models.Song.DoesNotExist: Song matching query does not exist.`
* **Evidence:** `musicapp/views.py:36`, `last_played_song = Song.objects.get(id=7)`
* **Root cause:** The view assumes a `Song` row with primary key `7` exists.
* **User-visible impact:** The homepage cannot render for a fresh migrated database.
* **Recovery priority:** Critical
* **Minimal repair direction:** Remove hardcoded fallback song lookup and allow `last_played` to be absent.
* **Required test:** `GET /` with zero `Song` rows returns 200 and shows an empty-library state.

### Finding 2

* **Finding:** All-songs page crashes with an empty song library.
* **Status:** Confirmed
* **Route:** `/all_songs/`
* **HTTP method:** GET
* **HTTP result:** Server error, 500-equivalent exception
* **Exception:** `musicapp.models.Song.DoesNotExist`
* **Evidence:** `musicapp/views.py:166`, `last_played_song = Song.objects.get(id=7)`
* **Root cause:** The view assumes a fallback `Song` row exists for anonymous visitors.
* **User-visible impact:** Users cannot browse the library when the database is empty.
* **Recovery priority:** Critical
* **Minimal repair direction:** Replace hardcoded fallback with optional context and empty-state rendering.
* **Required test:** `GET /all_songs/` with zero songs returns 200.

### Finding 3

* **Finding:** Hindi-song page crashes with an empty song library.
* **Status:** Confirmed
* **Route:** `/hindi_songs/`
* **HTTP method:** GET
* **HTTP result:** Server error, 500-equivalent exception
* **Exception:** `musicapp.models.Song.DoesNotExist`
* **Evidence:** `musicapp/views.py:84`, `last_played_song = Song.objects.get(id=7)`
* **Root cause:** The view assumes hardcoded Song ID `7`.
* **User-visible impact:** Language category page cannot render on a fresh database.
* **Recovery priority:** Critical
* **Minimal repair direction:** Use safe optional last-played context and an empty state.
* **Required test:** `GET /hindi_songs/` with zero songs returns 200.

### Finding 4

* **Finding:** English-song page crashes with an empty song library.
* **Status:** Confirmed
* **Route:** `/english_songs/`
* **HTTP method:** GET
* **HTTP result:** Server error, 500-equivalent exception
* **Exception:** `musicapp.models.Song.DoesNotExist`
* **Evidence:** `musicapp/views.py:107`, `last_played_song = Song.objects.get(id=7)`
* **Root cause:** The view assumes hardcoded Song ID `7`.
* **User-visible impact:** Language category page cannot render on a fresh database.
* **Recovery priority:** Critical
* **Minimal repair direction:** Use safe optional last-played context and an empty state.
* **Required test:** `GET /english_songs/` with zero songs returns 200.

### Finding 5

* **Finding:** Recent-history page crashes with an empty song library.
* **Status:** Confirmed
* **Route:** `/recent/`
* **HTTP method:** GET
* **HTTP result:** Server error, 500-equivalent exception
* **Exception:** `musicapp.models.Song.DoesNotExist`
* **Evidence:** `musicapp/views.py:209`, `last_played_song = Song.objects.get(id=7)`
* **Root cause:** The view assumes hardcoded Song ID `7`, even for anonymous users and empty history.
* **User-visible impact:** Recent-history page cannot render with empty data.
* **Recovery priority:** Critical
* **Minimal repair direction:** Require login or safely render anonymous/empty history without fallback song.
* **Required test:** `GET /recent/` with zero songs and anonymous user returns intended status.

### Finding 6

* **Finding:** Favourites page crashes for anonymous users.
* **Status:** Confirmed
* **Route:** `/favourite/`
* **HTTP method:** GET
* **HTTP result:** Server error, 500-equivalent exception
* **Exception:** `TypeError: 'AnonymousUser' object is not iterable`
* **Evidence:** `musicapp/views.py:307`, `Song.objects.filter(favourite__user=request.user, favourite__is_fav=True).distinct()`
* **Root cause:** User-specific query runs with `AnonymousUser` because the view lacks server-side login protection.
* **User-visible impact:** Anonymous users see a server error instead of redirect/login/empty state.
* **Recovery priority:** High
* **Minimal repair direction:** Add server-side login protection or explicit anonymous handling.
* **Required test:** Anonymous `GET /favourite/` redirects to login or returns the approved anonymous response.

### Finding 7

* **Finding:** Playlist page crashes for anonymous users.
* **Status:** Confirmed
* **Route:** `/playlist/`
* **HTTP method:** GET
* **HTTP result:** Server error, 500-equivalent exception
* **Exception:** `TypeError: 'AnonymousUser' object is not iterable`
* **Evidence:** `musicapp/views.py:287`, `Playlist.objects.filter(user=request.user).values('playlist_name').distinct`
* **Root cause:** User-specific query runs with `AnonymousUser`; the view also stores `.distinct` method rather than calling `.distinct()`, though the anonymous-user error occurs first.
* **User-visible impact:** Anonymous users see a server error.
* **Recovery priority:** High
* **Minimal repair direction:** Add server-side login protection and call `.distinct()` when playlist data is queried.
* **Required test:** Anonymous `GET /playlist/` redirects to login or returns approved anonymous response.

### Finding 8

* **Finding:** Playlist detail page crashes for anonymous users.
* **Status:** Confirmed
* **Route:** `/playlist/test-list/`
* **HTTP method:** GET
* **HTTP result:** Server error, 500-equivalent exception
* **Exception:** `TypeError: 'AnonymousUser' object is not iterable`
* **Evidence:** `musicapp/views.py:293`, `Song.objects.filter(playlist__playlist_name=playlist_name, playlist__user=request.user).distinct()`
* **Root cause:** User-specific query runs with `AnonymousUser` because the view lacks server-side login protection.
* **User-visible impact:** Anonymous users see a server error.
* **Recovery priority:** High
* **Minimal repair direction:** Add server-side login protection or explicit anonymous handling.
* **Required test:** Anonymous `GET /playlist/<name>/` redirects to login or returns approved anonymous response.

## 11. Working Behaviors

- Django development server can start on `127.0.0.1:8000`.
- `GET /mymusic/` returns 200.
- `GET /authentication/login/` returns 200.
- `GET /authentication/signup/` returns 200.
- `GET /accounts/login/` returns 200.
- `GET /authentication/logout/` redirects to `/`.
- `GET /admin/` redirects to the admin login page.
- Anonymous object-dependent routes guarded with `login_required` redirect to login:
  - `/1/`
  - `/play/1/`
  - `/play_song/1/`
  - `/play_recent_song/1/`
- Database row counts did not change during smoke testing.

## 12. Static Risks Not Reproduced

- Unsafe media `.url` access was not reproduced because the affected views crashed before templates reached media URL rendering, and no song records exist.
- Authenticated invalid-song handling was not reproduced because no users were created and `login_required` redirected anonymous requests before object lookup.
- GET-based recent-history mutation was not reproduced because anonymous requests to playback routes redirected before mutation logic ran.
- Playlist duplicate behavior was not reproduced because no users, songs, or playlists exist.
- Favourite duplicate behavior was not reproduced because no users or songs exist.
- Google OAuth provider behavior was not tested beyond rendering `/accounts/login/` and the custom auth templates.

## 13. Failure Priority

Priority order:

1. Critical: remove hardcoded fallback `Song.objects.get(id=7)` from public pages so empty database pages can render.
2. High: add server-side authentication handling to user-specific favourites and playlist pages.
3. High: repair `.distinct` usage in playlist queries after login protection is in place.
4. Medium: add missing-media-safe templates once pages can reach template rendering.
5. Medium: test authenticated invalid-object and playback-history behavior after a test user strategy is approved.

## 14. Recommended First Repair Branch

Recommended branch:

```text
fix/empty-library-safety
```

Scope included:

- Fix confirmed empty-library crashes caused by `Song.objects.get(id=7)`.
- Make `last_played` optional in affected views.
- Add empty states for:
  - homepage
  - all songs
  - Hindi songs
  - English songs
  - recent history
- Add tests proving these routes do not crash with zero songs.

Scope excluded:

- Playlist model redesign.
- Django or dependency upgrades.
- UI redesign.
- OAuth changes.
- Production deployment.
- Broad view refactoring.
- Favourite/playlist mutation redesign.
- Authenticated playback-history policy changes.

Files likely involved:

- `musicapp/views.py`
- `templates/musicapp/index.html`
- `templates/musicapp/all_songs.html`
- `templates/musicapp/hindi_songs.html`
- `templates/musicapp/english_songs.html`
- `templates/musicapp/recent.html`
- `musicapp/tests.py` or focused test modules if a test package is introduced.

Required tests:

- `GET /` with zero songs returns 200.
- `GET /all_songs/` with zero songs returns 200.
- `GET /hindi_songs/` with zero songs returns 200.
- `GET /english_songs/` with zero songs returns 200.
- `GET /recent/` with zero songs returns approved response.
- No test depends on real media files.

Acceptance criteria:

- No `Song.objects.get(id=7)` fallback remains in the repaired public-page path.
- Empty database public routes render useful empty states.
- Missing `last_played` does not crash templates.
- Django checks pass.
- Targeted tests and full test discovery pass.

## 15. Files Created or Modified

Created:

```text
PAGE_SMOKE_TEST_REPORT.md
```

No source files were modified.
No models, migrations, views, forms, URLs, templates, static files, settings, dependencies, `.env`, `.env.example`, or `.gitignore` files were modified.
No database rows were intentionally created, updated, or deleted.
No commit was created.
No push was performed.

## 16. Risks and Limitations

- Route requests were primarily executed with Django's test client after direct PowerShell process launch methods had environment issues.
- A live development server was successfully started and probed with `/authentication/login/`, but every route was not requested through the live TCP server.
- Authenticated behavior was not tested because the task prohibits creating users.
- Media rendering behavior remains unconfirmed because empty-library view errors occur first.
- The test suite still has zero tests.
- The app is not ready for user-facing browsing until empty-library crashes are repaired.

## 17. Recommended Next Task

Implement `fix/empty-library-safety` only.

The next task should remove the hardcoded fallback-song dependency and add tests for empty database rendering. It should not include authentication redesign, playlist model redesign, OAuth changes, UI redesign, dependency upgrades, or deployment work.
