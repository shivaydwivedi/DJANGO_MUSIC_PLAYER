# Playback History POST Mutation

## Objective

Remove all `Recent` playback-history mutations from GET requests and introduce
one authenticated, CSRF-protected, POST-only endpoint for recording plays.

## Previous GET Mutation Behavior

The old playback routes were:

```text
play/<int:song_id>/              play_song
play_song/<int:song_id>/         play_song_index
play_recent_song/<int:song_id>/  play_recent_song
```

Each route looked up the song, deleted any existing `Recent` row for the same
user/song pair, created a new `Recent` row, and redirected to its destination
page. Repeating a play moved the song to newest position by delete-and-create.

## HTTP Correctness Problem

GET requests should be safe and side-effect-free. Recording listening history on
GET meant link previews, refreshes, browser history navigation, or crawlers
could mutate `Recent` rows.

## POST-Only Contract

- GET requests never create, delete, reorder, or update `Recent`.
- Authenticated POST records a play.
- Anonymous POST redirects to login.
- Invalid song IDs return 404 without mutation.
- Repeat POST moves the song to newest position.
- One effective recent-history row per user/song remains.
- Other users' history remains untouched.
- Recent page ordering remains newest first.
- Historical duplicate rows are collapsed by the existing recent-page read path
  and cleaned for a user/song when that song is posted again.

The current schema still permits duplicate `Recent` rows because no uniqueness
constraint was added in this phase. Effective uniqueness is enforced in
application code by deleting current-user rows for the song inside a transaction
before creating the newest row.

## Route Design

New route:

```text
songs/<int:song_id>/record-play/  record_song_play
```

The existing playback route names remain for compatibility, but their GET
handlers no longer mutate history:

- `play_song` validates the song and redirects to `all_songs`;
- `play_song_index` validates the song and redirects to `index`;
- `play_recent_song` validates the song and redirects to `recent`.

## Safe Redirect Behavior

`record_song_play` accepts an optional `next` POST value. It uses the existing
safe redirect helper to allow only same-host safe URLs. External or malformed
targets are ignored.

Fallback destination is the song detail route.

## Duplicate Handling

`_record_recent_play(user, song)` runs inside `transaction.atomic()`:

1. delete all existing `Recent` rows for that user/song;
2. create one new row.

This preserves newest ordering by highest row ID and prevents duplicate
effective entries for the same user/song.

## Ordering Semantics

Recent ordering remains newest first. The existing recent-page helper still
collapses historical duplicates while preserving the newest occurrence.

## Template Changes

Play controls are POST forms:

- `templates/musicapp/partials/song_card.html`;
- `templates/musicapp/index.html`.

Each form posts to `record_song_play`, includes `{% csrf_token %}`, and includes
the current request path as a safe `next` target. Play controls are no longer
mutation anchors.

## CSRF Handling

All template play controls use standard Django forms with CSRF tokens. No
JavaScript was required.

Native audio controls were not wired to history recording in this phase. They
play media when available but do not mutate history on render, autoplay, refresh,
or browser navigation.

## Tests Added

Tests now cover:

- playback GET routes do not record history;
- playback GET routes do not reorder history;
- detail GET does not create history;
- recent GET does not mutate history;
- public song-list GET does not mutate history;
- authenticated POST records a play;
- anonymous POST redirects to login;
- invalid song ID returns 404 without mutation;
- repeat POST moves the song to newest;
- repeat POST leaves one row for user/song;
- historical duplicates are cleaned on POST;
- another user's history remains untouched;
- missing, blank, external, and safe internal `next` values;
- GET to record endpoint returns 405;
- play controls render as POST forms with CSRF;
- no play-history mutation route is rendered as a normal anchor;
- existing missing-media pages still render safely.

## Smoke Changes

The recovery smoke harness no longer permits GET playback mutation. It now:

- treats authenticated playback GET as read-only;
- adds anonymous protection for `record_song_play`;
- adds authenticated GET-to-record-route 405 coverage;
- adds invalid POST record coverage;
- adds a transactional POST record check that is rolled back by the harness.

Expected smoke count is now 41 checks.

## Manual Verification

Manual browser verification should use synthetic local data and clean it
afterward:

- opening song pages does not add history;
- refreshing song/player pages does not add history;
- clicking Play records history;
- repeated Play moves the song to newest;
- one effective row remains;
- Recent page updates correctly;
- a second user has separate history;
- browser back/refresh does not create extra entries;
- invalid song URL returns 404;
- external `next` cannot redirect away from the site;
- audio and missing-media fallbacks still work;
- mobile play controls remain usable.

## Migration Decision

No schema migration is required. A `Recent` uniqueness constraint is deferred
because this phase can enforce effective uniqueness in application code without
data cleanup or migration risk.

## Compatibility Notes

The legacy playback GET route names remain available and side-effect-free for
existing links. Templates now use the POST route for visible play controls.

## Current Limitations

- Native audio control play events do not record history.
- The database schema still allows duplicate `Recent` rows if written outside
  the application path.
- The compatibility GET routes still exist but are read-only redirects.

## Exact Next Branch

`modernization/recent-uniqueness-planning`

## Exactly One Next Task

Audit whether a future `Recent(user, song)` uniqueness constraint is worth the
data-cleanup and migration cost now that application-level recording is POST-only
and duplicate-safe.
