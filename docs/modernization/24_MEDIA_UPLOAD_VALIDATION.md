# Media Upload Validation

## Objective

Add focused validation for Sonica song cover and audio uploads without building
a media-processing pipeline or importing local commercial media files.

## Audit Findings

- `Song.song_img` and `Song.song_file` were plain `FileField` fields.
- `Pillow` is not installed in `.venv-django52`, so `song_img` remains a
  `FileField` instead of becoming an `ImageField`.
- `musicapp/forms.py` does not define a Song form. Django Admin uses the
  default model form for `Song`.
- Local uploaded media is configured with `MEDIA_ROOT = BASE_DIR / "media"` and
  `MEDIA_URL = "/media/"`.
- `.gitignore` ignores `media/*` and keeps `media/.gitkeep` tracked.
- Existing templates already guard `song_img` and `song_file` before rendering
  `.url`, so missing-media fallbacks remain safe.
- Existing migrations used `upload_to=""`, which stores uploaded files at the
  media root. Local ignored media files currently rely on that compatibility.

## Validation Rules

Audio uploads allow these extensions:

- `.mp3`
- `.wav`
- `.ogg`
- `.m4a`

Cover uploads allow these extensions:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`

Extension checks are case-insensitive and use the final filename suffix. A
deceptive filename such as `track.mp3.exe` is rejected because its final suffix
is `.exe`.

The validators do not trust or rely exclusively on browser-provided MIME types.
They also do not claim deep file-content inspection, antivirus scanning,
transcoding, waveform generation, or image decoding.

## Size Limits

Default limits are defined in `musicapp.validators`:

- audio: 20 MB;
- cover: 5 MB.

They can be overridden with Django settings:

- `SONICA_MAX_AUDIO_UPLOAD_SIZE`
- `SONICA_MAX_COVER_UPLOAD_SIZE`

Values are bytes.

## Enforcement Boundary

Reusable validators live in `musicapp.validators`.

`Song.clean()` calls the validators for `song_img` and `song_file`. This means
validation runs through Django `ModelForm` workflows, including Django Admin's
default Song form, and through explicit `full_clean()` calls.

Direct `Song.save()` does not call `full_clean()` automatically. This preserves
existing runtime and seed-data compatibility. Future upload views should call a
ModelForm or explicit validation before saving uploaded files.

## Storage Compatibility

No `upload_to` folder reorganisation was added. Existing root-level media paths
remain compatible and no files are moved.

`song_img` and `song_file` now explicitly allow blank values. This small
migration is required so existing media-less demo rows and admin/model-form
workflows can remain valid.

## Security And Filename Handling

The implementation relies on Django's storage layer for filename handling and
does not write custom path logic. User filenames are used only for extension
validation, not for execution or rendering decisions.

Local filesystem paths are not exposed in validation messages.

## Template Compatibility

No template redesign was required. Existing missing-cover and missing-audio
fallbacks are preserved on public pages, detail pages, favourites, playlists,
recent history, and the player partial.

## Tests Added

Tests cover:

- accepted audio extensions;
- rejected audio extensions;
- accepted cover extensions;
- rejected cover extensions;
- audio size limit;
- cover size limit;
- blank existing media fields;
- ModelForm validation;
- deceptive filenames;
- missing-media template regression;
- temporary test media storage instead of the real project `media/` directory.

## Migration

Created `musicapp/migrations/0008_allow_blank_song_media_fields.py`.

The migration changes only `blank=True` validation metadata on `song_img` and
`song_file` while preserving `upload_to=""`. It does not move existing media,
rename files, change storage paths, or import media.

## Deployment Limitations

This phase does not add persistent object storage, content scanning, media
transcoding, image resizing, or a media importer. Production deployments still
need durable uploaded-media storage and operational media backups.

## Local Media Privacy And Copyright

Files under `media/` are local, ignored runtime files and must not be committed.
Do not create Song records for local commercial media files in this phase. Keep
private, copyrighted, or user-supplied media out of Git.

## Next Branch

`modernization/song-admin-upload-ux`

## Next Task

Improve the Django Admin Song upload experience with clearer help text and
field grouping while preserving the validation contract from this phase.
