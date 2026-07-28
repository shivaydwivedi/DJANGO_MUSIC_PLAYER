# Favourite POST Mutation

## Objective

Move Favourite writes out of mixed-purpose page views and into dedicated
authenticated, CSRF-protected, POST-only endpoints. Favourite-related GET
requests are now read-only.

## Previous Mutation Behavior

Before this phase, `detail()` accepted POST payloads with `favorite_action=add`
or `favorite_action=remove`. The same view rendered song detail on GET and
mutated `Favourite` rows on POST.

The `favourite()` view rendered the current user's favourites on GET and also
removed favourites on POST using a submitted `song_id`.

No JavaScript was involved in Favourite mutation.

## Audit Findings

- `Favourite` fields are `id`, `user`, `song`, and `is_fav`.
- There is no database uniqueness constraint for `Favourite(user, song)`.
- Duplicate historical rows are possible.
- Active favourites are represented by `is_fav=True`.
- Inactive rows can exist as `is_fav=False`.
- Existing profile statistics count active rows with
  `Favourite.objects.filter(user=user, is_fav=True).count()`.
- Admin registration exposes `Favourite` through the default model admin.
- Homepage, song-list, Hindi, and English list GET views do not contain
  Favourite mutation controls.
- Favourite controls are rendered by `templates/musicapp/detail.html` and by
  `templates/musicapp/partials/song_card.html` on the favourites page.

## New POST-Only Contract

Two dedicated routes now own Favourite writes:

- `songs/<int:song_id>/favourite/add/`, route name `add_favourite`.
- `songs/<int:song_id>/favourite/remove/`, route name `remove_favourite`.

Both views use `@login_required(login_url='login')` and `@require_POST`.
Anonymous requests redirect to login before mutation. Authenticated GET
requests return 405 and leave row counts unchanged.

Existing public routes and the `favourite` route name are preserved. The
`detail` route name is also preserved, but `detail()` no longer mutates
favourites.

## Add Behavior

`add_favourite()` resolves the target `Song` with `get_object_or_404()`. Invalid
song IDs return 404 before any Favourite mutation.

The add operation is scoped to `request.user` and runs in a transaction. It
creates an active row when none exists. If a current-user row exists with
`is_fav=False`, that row is reactivated. If duplicate current-user rows exist,
one row is kept active and duplicate current-user rows for that song are
removed. Rows owned by other users are untouched.

This keeps duplicate add requests idempotent and prevents duplicate effective
favourites from remaining for the current user.

## Remove Behavior

The chosen remove policy is deletion. This matches the existing project
convention, which deleted active Favourite rows rather than toggling them to
false.

`remove_favourite()` resolves the target `Song` with `get_object_or_404()`.
Invalid song IDs return 404 before any Favourite mutation. For a valid song, all
current-user Favourite rows for that song are deleted. Removing a missing
favourite is a no-op and does not crash. Other users' rows and the `Song` record
are preserved.

## Safe Redirect Behavior

Both mutation views use the existing `authentication.compat.get_safe_redirect_url()`
helper. Safe same-host internal `next` values are honored. Missing, blank,
external, and protocol-relative external `next` values are rejected.

Fallbacks are deterministic:

- add falls back to the song detail page;
- remove falls back to the favourites page.

## Template And CSRF Changes

`templates/musicapp/detail.html` now posts add/remove Favourite actions directly
to `add_favourite` or `remove_favourite`, includes `{% csrf_token %}`, and
preserves the existing button styling and labels.

`templates/musicapp/favourite.html` now passes `remove_favourite` into the shared
song card partial.

`templates/musicapp/partials/song_card.html` now supports route-name based
remove actions and sends the current path as a safe `next` value. Mutation links
are not rendered as anchors.

Missing media fallbacks remain unchanged.

## Smoke Changes

`project_smoke_test` now checks:

- anonymous GET behavior for add/remove Favourite routes;
- authenticated GET 405 behavior for add/remove Favourite routes;
- transactional POST add Favourite behavior;
- transactional POST remove Favourite behavior.

All existing non-Favourite smoke checks were preserved.

## Tests Added

Focused tests cover read-only GET behavior, authentication, POST-only routes,
idempotent add, `is_fav=False` reactivation, duplicate cleanup, scoped remove,
missing remove, invalid IDs, safe redirects, CSRF-rendered forms, mutation anchor
absence, missing media rendering, smoke behavior, and playlist/playback
regression coverage.

## Manual Verification

Manual verification should use only synthetic users and songs. The verified
browser workflow is:

- opening and refreshing detail does not create Favourite rows;
- Add Favourite creates one active current-user row;
- repeated Add Favourite does not create an effective duplicate;
- the favourites page displays the song;
- Remove affects only the current user's Favourite rows;
- removing again does not crash;
- external and protocol-relative `next` values do not redirect off-site;
- invalid song actions return 404;
- missing media fallbacks still render.

Synthetic data must be cleaned up afterward.

## Migration Decision

No schema migration is required for this phase. A database uniqueness constraint
for `Favourite(user, song)` remains intentionally deferred until a copied-data
duplicate audit and migration plan are reviewed.

## Compatibility Notes

The `detail` and `favourite` route names remain available. Playlist behavior,
playback-history behavior, the legacy `Playlist` table, and media fallbacks were
not redesigned in this phase.

## Current Limitations

The database still does not enforce Favourite uniqueness. The application now
handles duplicate current-user rows during add/remove, but historical duplicate
data should be audited before adding a constraint.

## Next Branch

`modernization/favourite-uniqueness-planning`

## Next Task

Audit copied production-like Favourite data for duplicate `user, song` rows and
prepare a reviewed uniqueness-migration plan.
