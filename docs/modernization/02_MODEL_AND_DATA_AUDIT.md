# Model and Data Audit

## Model Inventory

| Model | Fields | Ownership |
| --- | --- | --- |
| `Song` | `name`, `album`, `language`, `song_img`, `year`, `singer`, `song_file` | Global catalog row. |
| `Playlist` | `user`, `playlist_name`, `song` | User-owned playlist membership row. |
| `Favourite` | `id`, `user`, `song`, `is_fav` | User-owned song preference row. |
| `Recent` | `user`, `song` | User-owned playback-history row. |

## Relationships

- `Playlist.user -> auth.User`
- `Playlist.song -> Song`
- `Favourite.user -> auth.User`
- `Favourite.song -> Song`
- `Recent.user -> auth.User`
- `Recent.song -> Song`

All foreign keys currently use cascade delete.

## Missing Database Constraints

The current schema has no explicit uniqueness constraints or supporting indexes
for the main user-owned relationships:

- `Favourite(user, song)` should eventually be unique.
- `Playlist(user, playlist_name, song)` should eventually be unique if the
  current membership-row model remains temporarily.
- A future playlist redesign should use a `Playlist` container and a separate
  membership model with uniqueness on `(playlist, song)`.
- `Recent(user, song)` is deduplicated by code today and could eventually be
  unique if the intended semantics remain "latest play per user/song".
- `Song` has no uniqueness for name/album/singer/year and no normalized artist
  model.

## Playlist Model Problem

The current `Playlist` model is not a playlist container. Each row means "this
song belongs to this named playlist for this user." As a result, a truly empty
named playlist cannot exist. When the final song is removed from a playlist, no
row remains and the `playlist_songs` route correctly returns 404 for that name.

The durable modernization target is a separate playlist container model, for
example:

- `Playlist`: user, name, timestamps, optional slug/display metadata.
- `PlaylistSong`: playlist, song, ordering/timestamps, unique `(playlist, song)`.

That redesign requires a migration and data migration, so it is deferred.

## Recent Semantics

Recent history currently means "the latest unique songs played by the user." On
playback recording, existing `Recent` rows for that user/song are deleted and a
new row is inserted. Ordering is therefore based on descending row id, not an
explicit timestamp.

This behavior is tested and stable, but modernization should add a timestamp if
the data model is revisited.

## Data Portability Notes

- SQLite is the active database backend.
- Existing migrations are simple and portable, but future PostgreSQL deployment
  should verify string comparison, case sensitivity, distinct queries, and
  index behavior.
- Local media files are not part of the repository and cannot be assumed to
  exist.
- Demo data intentionally creates media-less songs, so missing-media behavior is
  a first-class state.
