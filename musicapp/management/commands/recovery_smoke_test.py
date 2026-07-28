from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.test import Client
from django.urls import reverse

from musicapp.models import Favourite, Playlist, PlaylistContainer, PlaylistSong, Recent, Song


COUNT_MODELS = {
    'Song': Song,
    'Favourite': Favourite,
    'Playlist': Playlist,
    'PlaylistContainer': PlaylistContainer,
    'PlaylistSong': PlaylistSong,
    'Recent': Recent,
    'User': User,
}


@dataclass
class SmokeCheck:
    key: str
    route_name: str
    method: str
    url: str
    auth_state: str
    expected_status: int
    read_only: bool = True
    note: str = ''
    post_data: dict = None


def get_row_counts():
    return {
        name: model.objects.count()
        for name, model in COUNT_MODELS.items()
    }


def build_smoke_checks(auth_user):
    return [
        SmokeCheck('public:index', 'index', 'GET', reverse('index'), 'anonymous', 200),
        SmokeCheck('public:all_songs', 'all_songs', 'GET', reverse('all_songs'), 'anonymous', 200),
        SmokeCheck('public:hindi_songs', 'hindi_songs', 'GET', reverse('hindi_songs'), 'anonymous', 200),
        SmokeCheck('public:english_songs', 'english_songs', 'GET', reverse('english_songs'), 'anonymous', 200),
        SmokeCheck('public:recent', 'recent', 'GET', reverse('recent'), 'anonymous', 200),
        SmokeCheck('protected:mymusic', 'mymusic', 'GET', reverse('mymusic'), 'anonymous', 302),
        SmokeCheck('protected:favourite', 'favourite', 'GET', reverse('favourite'), 'anonymous', 302),
        SmokeCheck('protected:playlist', 'playlist', 'GET', reverse('playlist'), 'anonymous', 302),
        SmokeCheck('protected:playlist_songs', 'playlist_songs', 'GET', reverse('playlist_songs', args=[999]), 'anonymous', 302),
        SmokeCheck('protected:create_playlist', 'create_playlist', 'GET', reverse('create_playlist'), 'anonymous', 302),
        SmokeCheck('protected:rename_playlist', 'rename_playlist', 'GET', reverse('rename_playlist', args=[999]), 'anonymous', 302),
        SmokeCheck('protected:delete_playlist', 'delete_playlist', 'GET', reverse('delete_playlist', args=[999]), 'anonymous', 302),
        SmokeCheck('protected:add_song_to_playlist', 'add_song_to_playlist', 'GET', reverse('add_song_to_playlist', args=[999, 999]), 'anonymous', 302),
        SmokeCheck('protected:remove_song_from_playlist', 'remove_song_from_playlist', 'GET', reverse('remove_song_from_playlist', args=[999, 999]), 'anonymous', 302),
        SmokeCheck('protected:add_favourite', 'add_favourite', 'GET', reverse('add_favourite', args=[999]), 'anonymous', 302),
        SmokeCheck('protected:remove_favourite', 'remove_favourite', 'GET', reverse('remove_favourite', args=[999]), 'anonymous', 302),
        SmokeCheck('protected:detail', 'detail', 'GET', reverse('detail', args=[999]), 'anonymous', 302),
        SmokeCheck('protected:play_song', 'play_song', 'GET', reverse('play_song', args=[999]), 'anonymous', 302),
        SmokeCheck('protected:record_song_play', 'record_song_play', 'GET', reverse('record_song_play', args=[999]), 'anonymous', 302),
        SmokeCheck(
            'protected:play_song_index',
            'play_song_index',
            'GET',
            reverse('play_song_index', args=[999]),
            'anonymous',
            302,
        ),
        SmokeCheck(
            'protected:play_recent_song',
            'play_recent_song',
            'GET',
            reverse('play_recent_song', args=[999]),
            'anonymous',
            302,
        ),
        SmokeCheck('auth:login', 'login', 'GET', reverse('login'), 'anonymous', 200),
        SmokeCheck('auth:signup', 'signup', 'GET', reverse('signup'), 'anonymous', 200),
        SmokeCheck('auth:logout_get', 'logout', 'GET', reverse('logout'), 'anonymous', 405),
        SmokeCheck(
            'auth:logout_post',
            'logout',
            'POST',
            reverse('logout'),
            'anonymous',
            302,
            post_data={},
        ),
        SmokeCheck('auth_empty:mymusic', 'mymusic', 'GET', reverse('mymusic'), 'authenticated', 200),
        SmokeCheck('auth_empty:favourite', 'favourite', 'GET', reverse('favourite'), 'authenticated', 200),
        SmokeCheck('auth_empty:playlist', 'playlist', 'GET', reverse('playlist'), 'authenticated', 200),
        SmokeCheck('auth_empty:recent', 'recent', 'GET', reverse('recent'), 'authenticated', 200),
        SmokeCheck('invalid:detail', 'detail', 'GET', reverse('detail', args=[999]), 'authenticated', 404),
        SmokeCheck('invalid:play_song', 'play_song', 'GET', reverse('play_song', args=[999]), 'authenticated', 404),
        SmokeCheck('invalid:record_song_play', 'record_song_play', 'POST', reverse('record_song_play', args=[999]), 'authenticated', 404, post_data={}),
        SmokeCheck(
            'invalid:play_song_index',
            'play_song_index',
            'GET',
            reverse('play_song_index', args=[999]),
            'authenticated',
            404,
        ),
        SmokeCheck(
            'invalid:play_recent_song',
            'play_recent_song',
            'GET',
            reverse('play_recent_song', args=[999]),
            'authenticated',
            404,
        ),
        SmokeCheck(
            'invalid:playlist_songs',
            'playlist_songs',
            'GET',
            reverse('playlist_songs', args=[999]),
            'authenticated',
            404,
        ),
        SmokeCheck('post_only:create_playlist', 'create_playlist', 'GET', reverse('create_playlist'), 'authenticated', 405),
        SmokeCheck('post_only:rename_playlist', 'rename_playlist', 'GET', reverse('rename_playlist', args=[999]), 'authenticated', 405),
        SmokeCheck('post_only:delete_playlist', 'delete_playlist', 'GET', reverse('delete_playlist', args=[999]), 'authenticated', 405),
        SmokeCheck('post_only:add_song_to_playlist', 'add_song_to_playlist', 'GET', reverse('add_song_to_playlist', args=[999, 999]), 'authenticated', 405),
        SmokeCheck('post_only:remove_song_from_playlist', 'remove_song_from_playlist', 'GET', reverse('remove_song_from_playlist', args=[999, 999]), 'authenticated', 405),
        SmokeCheck('post_only:record_song_play', 'record_song_play', 'GET', reverse('record_song_play', args=[999]), 'authenticated', 405),
        SmokeCheck('post_only:add_favourite', 'add_favourite', 'GET', reverse('add_favourite', args=[999]), 'authenticated', 405),
        SmokeCheck('post_only:remove_favourite', 'remove_favourite', 'GET', reverse('remove_favourite', args=[999]), 'authenticated', 405),
        SmokeCheck(
            'playback_get:read_only',
            'play_song',
            'GET',
            '',
            'authenticated',
            302,
        ),
        SmokeCheck(
            'post:record_song_play',
            'record_song_play',
            'POST',
            '',
            'authenticated',
            302,
            read_only=False,
            post_data={'next': reverse('recent')},
            note='POST record-play route is the only playback history mutation path.',
        ),
        SmokeCheck(
            'post:add_favourite',
            'add_favourite',
            'POST',
            '',
            'authenticated',
            302,
            read_only=False,
            post_data={'next': reverse('favourite')},
            note='POST add-favourite route is the only favourite creation/reactivation path.',
        ),
        SmokeCheck(
            'post:remove_favourite',
            'remove_favourite',
            'POST',
            '',
            'authenticated',
            302,
            read_only=False,
            post_data={},
            note='POST remove-favourite route is the only favourite removal path.',
        ),
    ]


def _create_smoke_song():
    return Song.objects.create(
        name='Smoke Harness Song',
        album='Smoke Harness',
        language='English',
        year=2026,
        singer='Smoke Harness',
    )


def _prepare_playback_check(check):
    song = Song.objects.create(
        name='Smoke Harness Song',
        album='Smoke Harness',
        language='English',
        year=2026,
        singer='Smoke Harness',
    )
    check.url = reverse('play_song', args=[song.id])


def _prepare_record_play_check(check):
    song = _create_smoke_song()
    check.url = reverse('record_song_play', args=[song.id])


def _prepare_add_favourite_check(check):
    song = _create_smoke_song()
    check.url = reverse('add_favourite', args=[song.id])


def _prepare_remove_favourite_check(check, auth_user):
    song = _create_smoke_song()
    Favourite.objects.create(user=auth_user, song=song, is_fav=True)
    check.url = reverse('remove_favourite', args=[song.id])


def run_smoke_checks(expect_overrides=None):
    expect_overrides = expect_overrides or {}
    auth_user = User.objects.create_user(username='smoke-user', password='smoke-pass')
    checks = build_smoke_checks(auth_user)
    results = []
    http_host = '127.0.0.1' if settings.DEBUG else 'testserver'

    for check in checks:
        if check.key == 'playback_get:read_only':
            _prepare_playback_check(check)
        elif check.key == 'post:record_song_play':
            _prepare_record_play_check(check)
        elif check.key == 'post:add_favourite':
            _prepare_add_favourite_check(check)
        elif check.key == 'post:remove_favourite':
            _prepare_remove_favourite_check(check, auth_user)

        client = Client(HTTP_HOST=http_host)
        if check.auth_state == 'authenticated':
            client.force_login(auth_user)

        expected_status = expect_overrides.get(check.key, check.expected_status)
        before = get_row_counts()
        if check.method == 'POST':
            response = client.post(check.url, check.post_data or {})
        else:
            response = client.get(check.url)
        after = get_row_counts()

        changed_counts = {
            name: (before[name], after[name])
            for name in before
            if before[name] != after[name]
        }
        status_ok = response.status_code == expected_status
        mutation_ok = True if not check.read_only else not changed_counts
        passed = status_ok and mutation_ok
        results.append({
            'key': check.key,
            'route_name': check.route_name,
            'method': check.method,
            'auth_state': check.auth_state,
            'expected_status': expected_status,
            'actual_status': response.status_code,
            'read_only': check.read_only,
            'changed_counts': changed_counts,
            'mutation_ok': mutation_ok,
            'status_ok': status_ok,
            'passed': passed,
            'note': check.note,
        })

    return results


def render_report(results):
    lines = []
    header = (
        f"{'route':<24} {'method':<6} {'auth':<13} {'expect':<7} "
        f"{'actual':<7} {'mutation':<18} {'result':<5}"
    )
    lines.append(header)
    lines.append('-' * len(header))

    for result in results:
        mutation = 'allowed'
        if result['read_only']:
            mutation = 'unchanged' if result['mutation_ok'] else str(result['changed_counts'])
        status = 'PASS' if result['passed'] else 'FAIL'
        lines.append(
            f"{result['route_name']:<24} {result['method']:<6} {result['auth_state']:<13} "
            f"{result['expected_status']:<7} {result['actual_status']:<7} {mutation:<18} {status:<5}"
        )
        if result['note']:
            lines.append(f"  note: {result['note']}")

    total = len(results)
    passed = sum(1 for result in results if result['passed'])
    failed = total - passed
    lines.append('')
    lines.append(f"Total checks: {total}")
    lines.append(f"Passed checks: {passed}")
    lines.append(f"Failed checks: {failed}")
    lines.append(f"Overall result: {'PASS' if failed == 0 else 'FAIL'}")
    return '\n'.join(lines)


class Command(BaseCommand):
    help = 'Run the recovery smoke harness against disposable data.'

    def handle(self, *args, **options):
        with transaction.atomic():
            results = run_smoke_checks()
            self.stdout.write(render_report(results))
            transaction.set_rollback(True)

        failed = [result['key'] for result in results if not result['passed']]
        if failed:
            raise CommandError('Recovery smoke harness failed: {}'.format(', '.join(failed)))
