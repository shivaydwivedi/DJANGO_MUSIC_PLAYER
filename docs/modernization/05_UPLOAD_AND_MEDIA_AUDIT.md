# Upload and Media Audit

## Current Media Fields

`Song.song_img` and `Song.song_file` are plain `FileField` values. They have no
`upload_to`, `blank`, `null`, model validators, form validators, extension
checks, MIME checks, file-size checks, image decoding, or audio probing.

The database fields are required at the model layer, but existing tests and demo
data can create songs without assigned files. The UI now treats missing media as
a valid state and renders fallbacks.

## Current Safety Behavior

- Template `.url` access is guarded before rendering cover art or audio.
- Missing cover art renders a fallback.
- Missing audio renders an unavailable-audio state.
- No fake URLs or placeholder media files are created.

## Missing Upload Validation

The project currently does not validate:

- image extension allowlist,
- audio extension allowlist,
- MIME type,
- file size,
- decoded image dimensions,
- malicious SVG or HTML uploads,
- corrupt media files,
- duplicate uploaded files,
- orphaned files after song deletion or replacement.

## Media Serving Assumptions

Development uses `MEDIA_URL` and `MEDIA_ROOT` with debug-mode URL serving.
Production media storage, access control, CDN behavior, and cleanup are not
configured.

## Recommended Media Phase

Add upload validation in a dedicated phase after deciding whether media upload
is an admin-only feature or a user-facing feature. Keep missing-media fallbacks
permanent, because seeded demo data and imported catalog rows may continue to
have incomplete media.
