# Modernization Risk Register

| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Django/allauth upgrade breaks authentication flows | High | High | Replace deprecated APIs first, upgrade incrementally, test login/signup/profile/social-off states. |
| Playlist model redesign loses memberships | High | Medium | Add duplicate audit queries, write data migration tests, back up production data first. |
| Converting playback GET mutations changes UX | Medium | Medium | Keep legacy behavior until a dedicated playback phase with browser tests. |
| Upload validation rejects existing catalog media | Medium | Medium | Audit existing media before enforcing validators; preserve missing-media fallbacks. |
| Production settings remain local-development oriented | High | Medium | Harden settings before deployment and verify with `manage.py check --deploy` in a later phase. |
| Removing unused dependencies breaks legacy paths | Medium | Medium | Remove one group at a time and run clean install plus full test suite. |
| SQLite-to-PostgreSQL behavior differs | Medium | Medium | Add database portability checks and test migrations on PostgreSQL before production. |
| Lack of logging hides production failures | Medium | Medium | Add structured logging and release smoke checks before demo deployment. |

## Top Five Modernization Risks

1. Framework and allauth upgrade compatibility.
2. Playlist data migration from membership rows to containers.
3. Playback history currently being recorded by GET routes.
4. Missing upload/media validation becoming a security issue if uploads expand.
5. Production settings and storage assumptions not yet deployment-ready.
