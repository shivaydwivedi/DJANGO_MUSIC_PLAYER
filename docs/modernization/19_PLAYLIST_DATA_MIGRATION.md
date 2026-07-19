# Playlist Data Migration

## Objective

Copy legacy playlist membership rows into the normalized playlist schema while
leaving all runtime behavior on the legacy `Playlist` model.

Source schema:

- `Playlist.user`
- `Playlist.playlist_name`
- `Playlist.song`

Target schema:

- `PlaylistContainer.user`
- `PlaylistContainer.name`
- `PlaylistSong.playlist`
- `PlaylistSong.song`

## Legacy Data Audit

The local SQLite audit printed aggregate counts only:

| Metric | Count |
| --- | ---: |
| Users | 1 |
| Songs | 8 |
| Legacy playlist rows | 0 |
| Distinct `(user_id, playlist_name)` pairs | 0 |
| Distinct `(user_id, playlist_name, song_id)` memberships | 0 |
| Duplicate membership groups | 0 |
| Duplicate extra rows | 0 |
| Blank playlist names | 0 |
| Whitespace-only playlist names | 0 |
| Leading/trailing whitespace names | 0 |
| Case-only collision groups | 0 |
| Whitespace-normalization collision groups | 0 |
| Users owning playlists | 0 |
| Songs referenced by playlists | 0 |
| Normalized containers before migration | 0 |
| Normalized memberships before migration | 0 |
| Favourites | 0 |
| Recent rows | 1 |

Maximum legacy playlist-name length is 200.

No usernames, emails, playlist names, or song titles were recorded.

## Migration Policy

The migration preserves stored playlist names exactly.

- no trimming;
- no case normalization;
- no whitespace normalization;
- case-distinct names remain distinct;
- whitespace-distinct names remain distinct;
- blank names are migrated exactly if present;
- one container is created per exact `(user_id, playlist_name)` pair;
- one membership is created per distinct exact
  `(user_id, playlist_name, song_id)` membership;
- exact duplicate legacy rows collapse into one normalized membership;
- legacy rows are not changed or deleted;
- empty playlists are not invented because the legacy schema cannot represent
  them;
- timestamps use model defaults at migration time.

Exact-name preservation is safer than normalization in this phase because
normalization could merge playlists that users previously experienced as
different. Cleanup rules for case, whitespace, or blank names need a separate
product and data-quality decision.

## Migration Created

Created:

```text
musicapp/migrations/0007_backfill_normalized_playlist_data.py
```

The migration uses `migrations.RunPython(forwards, backwards)` and historical
models through `apps.get_model`.

## Forward Behavior

Forward migration:

- creates a migration-owned provenance table;
- iterates distinct legacy memberships in deterministic
  `user_id, playlist_name, song_id` order;
- reuses an existing normalized container for the same exact user/name;
- creates missing containers;
- reuses existing normalized memberships;
- creates missing memberships;
- records whether each container and membership was created by this migration.

The provenance table is not an application model and is not represented in
`models.py`.

## Backward Behavior

Reverse migration:

- reads migration provenance;
- deletes only memberships that this migration created;
- deletes only containers that this migration created and that are empty after
  membership deletion;
- leaves legacy rows untouched;
- leaves pre-existing matching normalized rows untouched;
- drops the migration-owned provenance table.

Rollback limitation: if future code mutates migrated normalized rows before
reversal, the migration can only use the recorded IDs and current emptiness to
decide what to delete. Later branches must review rollback safety before writing
runtime data to the normalized tables.

## Conflict Analysis

- Normalized tables empty: migrated rows are created.
- Matching container exists: reused safely.
- Matching membership exists: reused and not duplicated.
- Duplicate legacy membership rows: collapse into one normalized membership.
- Same name owned by different users: separate containers.
- Same song in different playlists: separate memberships.
- Case-different names: separate containers.
- Whitespace-different names: separate containers.
- Blank names: preserved exactly.
- Failed migration midway: Django migration transaction rolls back on supported
  SQLite behavior.
- Reverse with unrelated normalized data: provenance protects pre-existing rows.
- Manual re-run in tests: existing containers/memberships are reused.

## Copied-Database Rehearsal

A copy of the local SQLite database was created outside the repository and
deleted after rehearsal.

Before forward migration:

- integrity check: `ok`;
- `musicapp.0006` applied;
- `musicapp.0007` not applied;
- legacy rows: 0;
- distinct pairs: 0;
- distinct memberships: 0;
- duplicate groups: 0;
- normalized containers: 0;
- normalized memberships: 0;
- favourites: 0;
- recent rows: 1;
- songs: 8;
- users: 1.

After forward migration:

- integrity check: `ok`;
- `musicapp.0007` applied;
- legacy rows unchanged;
- normalized containers: 0;
- normalized memberships: 0;
- favourites, recent, songs, and users unchanged;
- no pending migrations.

Reverse rehearsal:

- an unrelated normalized container and membership were created on the copy;
- reversing to `0006` preserved that unrelated normalized data;
- legacy rows remained unchanged;
- integrity remained `ok`.

Reapply rehearsal:

- reapplying `0007` succeeded;
- unrelated normalized data remained;
- integrity remained `ok`.

## Fresh-Database Rehearsal

A fresh SQLite database outside the repository was migrated to latest, rolled
back to `musicapp.0006`, and populated with controlled synthetic legacy
fixtures.

Controlled fixture results:

- legacy rows: 7;
- forward containers: 5;
- forward memberships: 6;
- duplicate legacy memberships collapsed;
- case-distinct, whitespace-distinct, blank, and cross-user names remained
  separate;
- reverse preserved all 7 legacy rows and removed migrated normalized rows;
- latest migration reapplied successfully.

After reapplying latest:

- `seed_demo_data` created 8 demo songs on first run;
- second seed run reported 8 unchanged;
- full tests passed;
- recovery smoke checks passed.

## Tests Added

Migration tests cover:

- one legacy row creating one container and membership;
- multiple songs under one legacy name;
- multiple playlist names;
- same playlist name owned by different users;
- duplicate legacy rows collapsing;
- case-distinct names;
- whitespace-distinct names;
- blank names;
- existing matching container reuse;
- existing matching membership reuse;
- legacy rows remaining unchanged;
- ownership preservation;
- reverse preserving legacy rows;
- reverse preserving unrelated normalized data;
- empty legacy table forward migration;
- migration from `0006` to `0007`;
- migration reversal from `0007` to `0006`;
- reapplication after reverse;
- uniqueness constraints remaining valid;
- runtime views still using the legacy schema.

## Deferred Runtime Cutover

This phase does not switch views, forms, templates, profile statistics, admin
workflows, seed behavior, or smoke-test behavior. Runtime code still reads and
writes the legacy `Playlist` model.

## Exact Next Branch

`modernization/playlist-runtime-cutover`

## Exact Next Task

Switch playlist runtime views and templates to the normalized schema behind
tests while preserving existing user-facing playlist behavior.
