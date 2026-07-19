# Playlist Schema Foundation

## Current Legacy Playlist Audit

The existing legacy model remains in place:

```python
class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    playlist_name = models.CharField(max_length=200)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
```

Legacy behavior:

- playlist names are stored repeatedly in `Playlist.playlist_name`;
- each row represents one song membership in a named playlist;
- ownership is enforced in views by filtering `Playlist.user=request.user`;
- duplicates are still possible at the database level because no unique
  constraint exists on `(user, playlist_name, song)`;
- empty named playlists cannot exist because deleting the last membership row
  removes all data for that name;
- profile statistics count distinct legacy names and legacy membership rows;
- current templates render legacy names from `values('playlist_name').distinct()`;
- current smoke checks count legacy `Playlist` rows only.

Queries that still depend on the legacy schema:

- `musicapp.views.detail()`: distinct legacy playlist names and
  `Playlist.objects.get_or_create(...)`;
- `musicapp.views.playlist()`: distinct legacy playlist names;
- `musicapp.views.playlist_songs()`: legacy existence check, song lookup, and
  removal by `playlist_name`;
- `authentication.views.profile_request()`: distinct name count and legacy row
  count;
- tests and the recovery smoke harness that assert current behavior.

Templates that still depend on the legacy schema:

- `templates/musicapp/detail.html`
- `templates/musicapp/playlist.html`
- `templates/musicapp/playlist_songs.html`
- `templates/authentication/profile.html`

Seed/demo data does not create playlists. Admin previously registered the
legacy model only.

## Additive Schema

Added alongside the legacy model:

```python
class PlaylistContainer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PlaylistSong(models.Model):
    playlist = models.ForeignKey(PlaylistContainer, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
```

Database constraints:

- unique playlist container names per user: `(user, name)`;
- unique song membership per playlist: `(playlist, song)`.

Indexes:

- `(user, name)` on playlist containers;
- `(playlist, added_at)` on playlist song memberships.

Admin registration was added for both new models so the schema can be inspected
manually. No view, form, template, profile statistic, seed command, or smoke
harness behavior was switched to the new schema in this phase.

## Migration

Created additive migration:

```text
musicapp/migrations/0006_playlistcontainer_playlistsong_and_more.py
```

The migration creates new tables, indexes, and constraints. It does not rename,
delete, alter, or backfill the legacy `musicapp_playlist` table.

Copied-database rehearsal:

- copied the local SQLite database to a temporary directory;
- applied migrations against the copy using a temporary settings module;
- verified `musicapp_playlistcontainer` exists;
- verified `musicapp_playlistsong` exists;
- verified legacy `musicapp_playlist` still exists;
- verified the copied database had no pending migrations afterward;
- removed the temporary copy.

After copied-database verification, the additive migration was applied to the
local SQLite runtime.

## Tests Added

Schema foundation tests cover:

- a playlist container can exist without songs;
- playlist names are unique per user;
- the same playlist name can exist for different users;
- a song can appear only once per playlist container;
- the same song can belong to different playlist containers;
- creating legacy playlist rows does not backfill new container rows;
- legacy duplicate behavior remains unchanged.

## Deferred Work

This phase intentionally does not:

- migrate legacy playlist data;
- switch playlist views/forms/templates;
- switch profile statistics;
- update the smoke harness to count new tables;
- remove or rename the legacy `Playlist` model.

Migration risks for the next phase:

- legacy duplicate rows need a deterministic cleanup policy;
- legacy playlist names may differ only by whitespace or case;
- empty playlists cannot be recovered from legacy rows because they never
  existed in the old schema;
- data migration must preserve per-user ownership and avoid cross-user leakage.

## Rollback

Because the migration is additive, rollback is straightforward while the new
schema is unused by business logic:

```powershell
.\.venv-django52\Scripts\python.exe manage.py migrate musicapp 0005
```

Review data loss first if any later branch writes to `PlaylistContainer` or
`PlaylistSong`.

## Exact Next Branch

`modernization/playlist-data-migration`

## Exact Next Task

Add a copied-database legacy playlist data migration rehearsal that populates the
new playlist container schema without switching runtime views yet.

Update: this follow-up was completed on
`modernization/playlist-data-migration`.
