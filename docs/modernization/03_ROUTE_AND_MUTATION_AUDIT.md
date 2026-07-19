# Route and Mutation Audit

## Public Read Routes

- `/`
- `/all_songs/`
- `/recent/`
- `/hindi_songs/`
- `/english_songs/`

Public browsing is intentionally preserved. Anonymous users see empty personal
state where appropriate.

## Protected Read Routes

- `/<song_id>/`
- `/mymusic/`
- `/playlist/`
- `/playlist/<playlist_name>/`
- `/favourite/`
- `/authentication/profile/`

These are login protected in the current code.

## POST Mutation Routes

- `/<song_id>/`: playlist add/create and favourite add/remove.
- `/playlist/<playlist_name>/`: remove a song from the current user's playlist.
- `/favourite/`: remove a song from the current user's favourites.
- `/authentication/profile/`: update username/email.
- `/authentication/logout/`: logout via POST.
- `/authentication/login/` and `/authentication/signup/`: authentication form
  submission.

Recent repair work made collection mutations explicit, POST-only, scoped to the
current user, and tolerant of invalid input.

## Remaining GET Mutations

Playback recording still occurs through these login-protected GET routes:

- `/play/<song_id>/`
- `/play_song/<song_id>/`
- `/play_recent_song/<song_id>/`

Each route fetches a song, records recent playback for the authenticated user,
and redirects back to the intended page. This is documented legacy behavior and
is also represented in the smoke harness.

## Playback Record Flow

`_record_recent_playback(user, song)` deletes the current user's existing
`Recent` row for that song, then creates a new row. This gives one current row
per user/song and uses the newest row id as ordering.

Invalid song ids are handled by `get_object_or_404` in the playback routes.

## Search Behavior

Song catalog pages use GET query parameters for filtering only. Recent-history
search filters the current user's already-scoped recent-song list in memory and
does not create, delete, or reorder rows.

## Authorization Notes

- Favourites, playlists, profile, and recent mutations are scoped by
  `request.user`.
- Cross-user favourite and playlist modifications are blocked at the query
  level.
- Public song browsing remains available.

## Route Modernization Recommendations

1. Keep current public browsing URLs stable.
2. Convert playback history writes from GET to POST only in a later UX/API
   phase, because this changes button/link semantics and smoke expectations.
3. Add explicit route names and tests for any future playlist container model.
4. Keep all user-owned collection mutations protected by authentication and CSRF.
