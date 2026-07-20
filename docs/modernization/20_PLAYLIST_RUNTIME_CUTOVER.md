# Playlist Runtime Cutover

## Objective

Switch runtime playlist behavior from the legacy `Playlist` membership-row
model to the normalized `PlaylistContainer` and `PlaylistSong` models.

The legacy model and table remain intact as rollback protection. This phase does
not remove or alter legacy data.

## Previous Legacy Runtime Behavior

- playlist names were repeated on each `Playlist` membership row;
- a named playlist could not exist without at least one song row;
- song detail created or added playlist rows by posting `playlist_name`;
- playlist detail used a name-based URL;
- removing the final song removed the effective playlist;
- profile statistics counted distinct legacy names and legacy rows.

## Normalized Runtime Contract

- playlist list reads `PlaylistContainer` records scoped to the authenticated
  user;
- playlist detail reads `PlaylistSong` memberships scoped through the owned
  container;
- playlist creation, rename, delete, add, and remove are POST-only;
- playlist IDs are used for normalized routes;
- empty playlists are first-class and remain visible;
- legacy `Playlist` rows are not written or back-synced.

## URL Decisions

The existing `playlist` and `playlist_songs` route names are preserved.

Normalized runtime routes:

```text
playlist/                                      playlist
playlist/create/                              create_playlist
playlist/<int:playlist_id>/                   playlist_songs
playlist/<int:playlist_id>/rename/            rename_playlist
playlist/<int:playlist_id>/delete/            delete_playlist
playlist/<int:playlist_id>/songs/<int:song_id>/add/     add_song_to_playlist
playlist/<int:playlist_id>/songs/<int:song_id>/remove/  remove_song_from_playlist
```

The old name-based `playlist/<str:playlist_name>/` route was replaced rather
than retained as a compatibility redirect. Internal links and tests now use
container IDs.

## View Changes

- `musicapp.views.playlist()` lists owned containers with annotated song counts.
- `musicapp.views.playlist_songs()` loads an owned container by ID and renders
  its memberships in deterministic membership order.
- `create_playlist()` trims names, rejects blank/whitespace-only names, rejects
  overlong names, rejects duplicate names for the same user, and creates an
  empty container.
- `add_song_to_playlist()` uses `get_or_create()` for idempotent normalized
  membership creation.
- `remove_song_from_playlist()` deletes the membership if present and leaves the
  container intact.
- `rename_playlist()` trims names and rejects duplicate names for the same user.
- `delete_playlist()` deletes the container and its memberships only.

All playlist object lookups are scoped to `request.user`.

## Template Changes

- `templates/musicapp/detail.html` lists normalized containers and posts add
  actions to ID-based add routes.
- `templates/musicapp/playlist.html` includes create, rename, and delete forms
  with CSRF tokens and displays song counts.
- `templates/musicapp/playlist_songs.html` renders the normalized container name,
  POST-only remove actions, and a retained empty playlist state.
- `templates/musicapp/partials/song_card.html` accepts an explicit remove form
  action while preserving existing media guards.

## Profile Statistics

Profile counts now use normalized user-scoped queries:

- playlist count = owned `PlaylistContainer` rows;
- playlist-song count = owned `PlaylistSong` memberships.

Favourite and recent-history statistics were not changed.

## Admin Support

The legacy `Playlist` admin remains registered and labelled through
`LegacyPlaylistAdmin` behavior. Normalized admin registrations now expose
container ownership, names, song counts, memberships, search, and filters.

## Smoke-Test Changes

The recovery smoke harness now counts `PlaylistContainer` and `PlaylistSong`
rows during read-only checks. Playlist checks use ID-based routes, and GET
requests to mutation routes are expected to return 405 for authenticated users.

The expected smoke count is now 37 checks.

## Legacy Isolation Results

Runtime playlist views, templates, profile statistics, and user mutations no
longer depend on `Playlist.objects`. Remaining legacy references are limited to:

- legacy model definition;
- admin-only legacy visibility;
- historical migrations;
- migration/schema tests;
- documentation.

Legacy rows are not changed by normalized create, add, remove, rename, or delete
operations.

## Rollback Boundary

Runtime is normalized-only after this phase. The legacy table is frozen
historical data and is not back-synced from normalized runtime writes.

Rollback to legacy runtime is safe only before users create or modify normalized
playlists after cutover. After normalized-only writes occur, reverting runtime
code alone would hide those new playlist changes unless a deliberate reverse
sync migration is designed. That reverse sync is outside this phase.

## Manual Verification Results

Local browser verification was run against `127.0.0.1:8002` with synthetic test
data. The browser pass confirmed:

- login as a temporary local user;
- authenticated homepage rendering;
- playlist list empty state;
- creating an empty playlist from the playlist page;
- trimmed playlist name display;
- empty playlist visible with `0 songs`;
- song detail showing normalized add action;
- missing cover and audio fallbacks on detail and playlist detail;
- adding a song to the playlist;
- adding the same song again without a duplicate-facing crash;
- playlist list updating to `1 song`;
- playlist detail rendering by ID;
- removing the only song;
- playlist detail remaining available with the empty state.

The browser session dropped before rename/delete/cross-user checks could be
completed interactively. Those paths are covered by automated tests in this
phase.

## Tests Added

Runtime tests now cover:

- anonymous playlist protection;
- current-user playlist list visibility;
- empty playlist creation and rendering;
- blank, whitespace-only, duplicate, and overlong name rejection;
- same playlist name for different users;
- normalized add behavior and duplicate-add idempotency;
- same song in different playlists;
- remove behavior with missing memberships;
- final-song removal preserving the container;
- rename trimming and duplicate handling;
- delete ownership and song preservation;
- POST-only mutation routes;
- song detail normalized container listing;
- profile statistics through normalized models;
- legacy row isolation during normalized operations.

## Current Limitations

- legacy rows remain present for rollback and historical audit;
- normalized changes are not back-synced to legacy rows;
- old name-based playlist URLs are not retained.

## Legacy Retirement Planning

The follow-up branch `modernization/playlist-legacy-retirement` documents the
safe retirement policy for the legacy `Playlist` model and table. It defers
destructive deletion to `modernization/drop-legacy-playlist` until confidence
criteria, copied-database audit, backup verification, and rollback policy are
approved.

## Exact Next Branch

`modernization/playback-history-post-mutation`

## Exactly One Next Task

Move playback/recent-history mutation off GET routes and onto POST-only actions.
