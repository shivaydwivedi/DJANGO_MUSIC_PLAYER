# Playlist Legacy Retirement Plan

## Objective

Define when and how the legacy `Playlist` model and `musicapp_playlist` table
can be retired safely after the normalized playlist runtime cutover.

This phase is documentation and policy only. It does not remove the legacy
model, drop the table, create a migration, change runtime behavior, change admin
behavior, or mutate playlist data.

## Current State

- Python 3.12.13 and Django 5.2.16 are the supported runtime.
- Normalized playlist runtime is active.
- `PlaylistContainer` and `PlaylistSong` are the only runtime playlist models.
- The legacy `Playlist` model and table still exist.
- Legacy `Playlist` rows are frozen historical data.
- Runtime writes are normalized-only and are not back-synced to legacy rows.
- No runtime playlist view, template, profile statistic, or mutation depends on
  legacy `Playlist`.

## Aggregate Audit Results

Local database audit output used aggregate counts only:

| Metric | Count |
| --- | ---: |
| Legacy `Playlist` rows | 0 |
| `PlaylistContainer` rows | 0 |
| `PlaylistSong` rows | 0 |
| Distinct legacy `(user_id, playlist_name)` pairs | 0 |
| Distinct legacy `(user_id, playlist_name, song_id)` memberships | 0 |

No usernames, emails, playlist names, song titles, or private identifiers were
printed or documented.

## Remaining Reference Classification

| Reference area | Classification | Retirement action |
| --- | --- | --- |
| `musicapp/models.py` legacy `Playlist` class | Model definition | Remove only in final destructive branch. |
| `musicapp/admin.py` `LegacyPlaylistAdmin` and registration | Admin-only reference | Keep during rollback-confidence period; remove or make read-only before final drop. |
| `musicapp/migrations/0002_playlist.py` | Historical migration | Keep permanently as migration history. |
| `musicapp/migrations/0007_backfill_normalized_playlist_data.py` | Historical migration | Keep permanently while migration history remains linear. |
| `musicapp/tests.py` migration executor tests using `LegacyPlaylist` | Migration test | Keep while migration 0007 remains meaningful. |
| `musicapp/tests.py` legacy schema tests | Schema test | Remove or replace when the legacy model is dropped. |
| `musicapp/tests.py` runtime-isolation tests using legacy rows | Runtime-isolation test | Remove or replace when the legacy table is dropped. |
| `musicapp/tests.py` and `authentication/tests.py` legacy row counts | Smoke/no-mutation guard | Remove when the table is dropped. |
| `musicapp/management/commands/project_smoke_test.py` legacy count guard | Smoke/no-mutation guard | Remove when the table is dropped. |
| `templates/musicapp/detail.html` and `templates/musicapp/playlist.html` `playlist_name` inputs | Runtime normalized form field | Keep; this names submitted playlist text, not the legacy table. |
| `musicapp/views.py` local variable `playlist_name` | Runtime normalized form handling | Keep; this validates normalized `PlaylistContainer.name`. |
| Modernization docs and historical audits | Documentation | Keep or update as historical context. |

No obsolete runtime references were found. Some older docs describe behavior that
was true in earlier phases; those are historical records, not runtime defects.

## Runtime Legacy-Free Confirmation

No `Playlist.objects` usage remains in:

- playlist runtime views;
- playlist templates;
- authentication profile statistics;
- normalized playlist mutation paths.

The only runtime-looking `playlist_name` references are normalized create/rename
form inputs and local variables.

## Why Deletion Is Deferred

The legacy table is unused, but it is still the simplest historical rollback
source immediately after the normalized runtime cutover. Deleting it now would
make the first destructive playlist phase irreversible without a database backup
or explicit archival mechanism.

Keeping an unused rollback table temporarily is safer because:

- it preserves migrated historical source data;
- it allows comparison between old and new schemas during the confidence period;
- it gives the project time to detect normalized runtime defects;
- it avoids destructive change before rollback policy is approved.

## Retirement Policy

1. Do not drop the legacy model or table in this branch.
2. Keep the table through at least one confidence phase after normalized runtime
   cutover.
3. Treat legacy data as frozen and read-only.
4. Do not back-sync normalized writes into legacy rows.
5. Before deletion, explicitly decide whether rollback to legacy runtime is
   still supported.
6. If rollback is no longer supported, document that decision clearly.
7. If rollback must remain supported, build a separate reverse-sync or export
   mechanism before deletion.
8. Make and verify a database backup before any destructive migration.
9. Rehearse the destructive migration on a copied database first.
10. Remove or make read-only legacy admin exposure before the final drop.
11. Remove obsolete legacy-count guards only when the table is actually retired.
12. Preserve historical migrations and useful migration tests where still
   meaningful.

## Confidence Criteria

All criteria must be satisfied before starting the final drop branch:

- normalized runtime has been stable through one release window or equivalent
  confidence period;
- no runtime code imports, queries, or writes legacy `Playlist`;
- no templates depend on legacy playlist fields;
- no profile statistics use legacy rows;
- no playlist routes use legacy names;
- all normalized ownership tests pass;
- all normalized mutation tests pass;
- 164 or more automated tests pass;
- all 37 project smoke checks pass;
- no production errors are attributable to normalized playlist runtime;
- there is no need to roll back to legacy runtime;
- copied-database audit shows every relevant legacy membership is represented
  in normalized data or explicitly accounted for;
- normalized-only changes are understood and protected;
- final database backup exists and is verified;
- destructive migration rehearsal succeeds;
- rollback or irreversibility policy is approved;
- admin exposure is removed or read-only;
- no private data is exposed in audit output.

## Final Copied-Database Audit

Immediately before deletion, run the audit on a copied database outside the
repository. Record aggregate counts only:

- legacy `Playlist` row count;
- distinct legacy `(user_id, playlist_name)` pairs;
- distinct legacy `(user_id, playlist_name, song_id)` memberships;
- duplicate legacy membership count;
- normalized container count;
- normalized membership count;
- legacy memberships missing from normalized schema;
- normalized containers with no legacy equivalent;
- normalized memberships with no legacy equivalent;
- users represented in both schemas;
- songs represented in both schemas;
- database integrity status;
- migration state;
- `Favourite` count;
- `Recent` count;
- `Song` count;
- `User` count.

Do not reveal private names, emails, playlist names, song titles, or raw record
identifiers.

## Audit Interpretation

- Legacy-only records: investigate before deletion; either backfill them,
  document why they are intentionally abandoned, or stop the deletion.
- Normalized-only records: expected after runtime cutover; protect them because
  the legacy schema cannot represent all normalized behavior.
- Duplicate legacy rows: expected to collapse to one normalized membership under
  migration 0007 policy.
- Blank or whitespace names: preserve prior migration interpretation; do not
  normalize during retirement.
- Case-distinct names: treat as distinct unless a separate product decision
  approves normalization.
- Missing songs or users: stop and resolve referential integrity before deletion.
- Post-cutover normalized changes: authoritative under the recommended policy.

## Data-Retention Policy

Before destructive retirement:

- create a verified database backup;
- store any required aggregate audit output without private values;
- avoid adding database copies or backups to Git;
- document backup location and verification outside the repository if the backup
  contains private data;
- delete temporary copied databases after rehearsal.

## Admin-Retirement Policy

Safe sequence:

1. Keep current legacy admin visibility during the immediate rollback-confidence
   period.
2. Later remove or make the legacy admin read-only.
3. Clearly label it as legacy while still present.
4. Prevent new legacy edits before the final destructive branch.
5. Confirm normalized admin is authoritative.
6. Remove legacy admin registration when the final drop migration is prepared.

No admin code changes are made in this branch.

## Rollback Choice A: End Legacy Rollback Support

Policy:

- normalized schema becomes authoritative;
- legacy runtime rollback is declared unsupported;
- legacy table is backed up;
- destructive migration is rehearsed;
- model and table are removed;
- historical migrations remain;
- rollback means restoring a database backup, not merely reverting code.

## Rollback Choice B: Preserve Legacy Rollback Support

Policy:

- design a reverse-sync or export process before deletion;
- define how empty normalized playlists are represented in the legacy row-based
  schema;
- define how renamed playlists are represented;
- define how deleted playlists are represented;
- define duplicate behavior;
- document normalized-only timestamps and ordering limitations;
- rehearse reverse sync;
- verify ownership;
- do not drop the legacy table until reverse-sync reliability is proven.

## Recommended Rollback Choice

Recommend Choice A after the confidence period.

The legacy schema cannot faithfully represent normalized behavior because:

- empty playlists have no row representation;
- playlist containers have timestamps that legacy rows do not preserve;
- memberships have `added_at` ordering that legacy rows do not preserve;
- deleted normalized playlists cannot be reconstructed from frozen legacy rows;
- renamed normalized playlists are not back-synced;
- normalized-only playlists and memberships created after cutover do not exist in
  legacy data.

Choice B is possible only with a new reverse-sync/export design, and that would
be a separate project with meaningful data-policy decisions.

## Destructive Migration Plan

Future branch: `modernization/drop-legacy-playlist`.

That branch should:

- re-run the full legacy-reference audit;
- make a verified database backup;
- rehearse on a copied SQLite database;
- remove `Playlist` from admin;
- remove the legacy model from `musicapp/models.py`;
- create one explicit migration that drops the legacy model/table;
- update tests and smoke guards;
- update documentation;
- verify fresh migration from zero;
- verify upgrade migration from an existing copied database;
- confirm normalized rows remain unchanged;
- confirm `Song`, `Favourite`, `Recent`, `User`, and media data remain
  unchanged;
- run all tests and smoke checks;
- run production checks;
- document whether reverse migration is supported.

Do not create that migration now.

## Migration Reversibility Limitations

Recreating an empty legacy table is not true rollback.

Django may be able to reverse a `DeleteModel` by recreating schema, but deleted
rows are not restored by schema recreation. Real rollback after table deletion
requires a verified database backup, an archival table, or an explicit data
export/import process.

Honest policy for this project: treat the eventual destructive migration as
operationally irreversible for data unless a verified backup restore is used.

## Backup Requirements

Before the destructive branch applies the drop migration to any meaningful
database:

- create a database backup outside Git;
- verify the backup can be read or restored;
- record only aggregate verification results in project docs;
- keep backup paths and private contents out of the repository.

## Rehearsal Requirements

Rehearse on a copied database outside the repository:

- record aggregate pre-drop counts;
- apply the drop migration;
- verify normalized playlist data is unchanged;
- verify non-playlist data is unchanged;
- run integrity checks;
- run tests and smoke checks;
- test backup restore or document the approved irreversibility policy;
- delete temporary copies afterward.

## Deletion Acceptance Criteria

- Confidence criteria are satisfied.
- Final copied-database audit is clean or explicitly approved.
- Backup is verified.
- Admin legacy exposure is removed or read-only.
- Runtime remains legacy-free.
- Final drop migration rehearsal succeeds.
- Tests and smoke checks pass.
- Production checks pass.
- No private data is exposed.
- Deletion/rollback policy is approved.

## Post-Deletion Verification

After the final destructive branch:

- `python manage.py check` passes;
- `python manage.py makemigrations --check --dry-run` reports no changes;
- `python manage.py migrate --plan` reports no unexpected operations;
- full tests pass;
- project smoke checks pass;
- production-like checks pass;
- no `Playlist` runtime/admin imports remain;
- normalized rows remain unchanged;
- `Song`, `Favourite`, `Recent`, `User`, media, authentication, and playback
  behavior remain unchanged.

## Current Limitations

- Legacy table still exists.
- Legacy admin remains visible.
- Smoke and no-mutation guards still count the legacy table.
- Normalized-only writes are not represented in legacy rows.
- Legacy rollback is only safe before meaningful normalized-only changes, unless
  a reverse-sync/export process is built.

## Exact Future Destructive Branch

`modernization/drop-legacy-playlist`

## Exact Next Engineering Branch

`modernization/playback-history-post-mutation`

## Exactly One Next Task

Move playback/recent-history mutation off GET routes and onto POST-only actions,
because it fixes a current HTTP correctness and security issue while the legacy
playlist drop waits for its confidence criteria.
