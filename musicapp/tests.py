import shutil
import tempfile
from io import StringIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from musicapp.management.commands.seed_demo_data import DEMO_ALBUM, DEMO_SONGS
from musicapp.management.commands.recovery_smoke_test import (
    render_report,
    run_smoke_checks,
)

from .models import Favourite, Playlist, Recent, Song


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class EmptyLibraryPageTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def _counts(self):
        return {
            'songs': Song.objects.count(),
            'recent': Recent.objects.count(),
            'favourites': Favourite.objects.count(),
            'playlists': Playlist.objects.count(),
        }

    def _create_song(self, name='Synthetic Test Song'):
        return Song.objects.create(
            name=name,
            album='Recovery Album',
            language='English',
            song_img=SimpleUploadedFile('cover.jpg', b'cover-bytes', content_type='image/jpeg'),
            year=2026,
            singer='Test Singer',
            song_file=SimpleUploadedFile('song.mp3', b'audio-bytes', content_type='audio/mpeg'),
        )

    def _create_song_with_media_state(self, name, language='English', with_image=False, with_audio=False):
        kwargs = {
            'name': name,
            'album': 'Recovery Album',
            'language': language,
            'year': 2026,
            'singer': 'Test Singer',
        }
        if with_image:
            kwargs['song_img'] = SimpleUploadedFile(
                name.replace(' ', '-').lower() + '.jpg',
                b'cover-bytes',
                content_type='image/jpeg',
            )
        if with_audio:
            kwargs['song_file'] = SimpleUploadedFile(
                name.replace(' ', '-').lower() + '.mp3',
                b'audio-bytes',
                content_type='audio/mpeg',
            )
        return Song.objects.create(**kwargs)

    def test_anonymous_public_pages_render_with_empty_library(self):
        routes = [
            (reverse('index'), 'The catalog has no songs yet.'),
            (reverse('all_songs'), 'The catalog has no songs yet.'),
            (reverse('hindi_songs'), 'The catalog has no Hindi songs yet.'),
            (reverse('english_songs'), 'The catalog has no English songs yet.'),
            (reverse('recent'), 'No recent songs yet.'),
        ]

        for url, expected_text in routes:
            with self.subTest(url=url):
                before = self._counts()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_text)
                self.assertEqual(self._counts(), before)

    def test_player_empty_state_renders_without_last_played(self):
        for url in [reverse('index'), reverse('all_songs'), reverse('recent')]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'No song is ready to play yet.')

    def test_authenticated_pages_render_with_no_history_or_songs(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        self.client.force_login(user)
        routes = [
            reverse('index'),
            reverse('all_songs'),
            reverse('hindi_songs'),
            reverse('english_songs'),
            reverse('recent'),
        ]

        for url in routes:
            with self.subTest(url=url):
                before = self._counts()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self._counts(), before)

    def test_non_empty_song_library_still_renders_song_cards(self):
        song = self._create_song()

        response = self.client.get(reverse('all_songs'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('detail', args=[song.id]))
        self.assertContains(response, 'cover')
        self.assertEqual(Song.objects.count(), 1)
        self.assertEqual(Recent.objects.count(), 0)

    def test_last_played_missing_media_renders_fallbacks(self):
        user = User.objects.create_user(username='blank-media-listener', password='secret-pass')
        song = Song.objects.create(
            name='Blank Media Song',
            album='Recovery Album',
            language='English',
            year=2026,
            singer='Test Singer',
        )
        Recent.objects.create(user=user, song=song)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('index'), {'q': 'no matching song'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cover unavailable')
        self.assertContains(response, 'Audio unavailable.')
        self.assertEqual(self._counts(), before)

    def test_anonymous_favourite_page_requires_login(self):
        song = self._create_song()
        before = self._counts()

        get_response = self.client.get(reverse('favourite'))
        post_response = self.client.post(reverse('favourite'), {'song_id': song.id})

        self.assertEqual(get_response.status_code, 302)
        self.assertEqual(post_response.status_code, 302)
        self.assertIn(reverse('login'), get_response['Location'])
        self.assertIn(reverse('login'), post_response['Location'])
        self.assertEqual(self._counts(), before)

    def test_detail_get_does_not_create_favourite(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Favourite.objects.count(), 0)

    def test_detail_add_favourite_is_idempotent(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        first_response = self.client.post(reverse('detail', args=[song.id]), {'favorite_action': 'add'})
        second_response = self.client.post(reverse('detail', args=[song.id]), {'favorite_action': 'add'})

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(Favourite.objects.filter(user=user, song=song, is_fav=True).count(), 1)

    def test_detail_remove_favourite_is_scoped_to_current_user(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        song = self._create_song()
        Favourite.objects.create(user=owner, song=song, is_fav=True)
        Favourite.objects.create(user=other_user, song=song, is_fav=True)
        self.client.force_login(owner)

        response = self.client.post(reverse('detail', args=[song.id]), {'favorite_action': 'remove'})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Favourite.objects.filter(user=owner, song=song, is_fav=True).exists())
        self.assertTrue(Favourite.objects.filter(user=other_user, song=song, is_fav=True).exists())

    def test_favourite_page_lists_only_current_user_songs(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        owner_song = self._create_song(name='Owner Favourite')
        other_song = self._create_song(name='Other Favourite')
        Favourite.objects.create(user=owner, song=owner_song, is_fav=True)
        Favourite.objects.create(user=other_user, song=other_song, is_fav=True)
        self.client.force_login(owner)

        response = self.client.get(reverse('favourite'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Owner Favourite')
        self.assertNotContains(response, 'Other Favourite')

    def test_favourite_remove_requires_valid_song_id(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        self.client.force_login(user)

        for payload, expected_status in [
            ({}, 400),
            ({'song_id': 'abc'}, 400),
            ({'song_id': '999'}, 404),
        ]:
            with self.subTest(payload=payload):
                before = self._counts()
                response = self.client.post(reverse('favourite'), payload)
                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(self._counts(), before)

    def test_favourite_remove_does_not_delete_another_users_record(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        song = self._create_song()
        Favourite.objects.create(user=owner, song=song, is_fav=True)
        self.client.force_login(other_user)

        response = self.client.post(reverse('favourite'), {'song_id': song.id})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Favourite.objects.filter(user=owner, song=song, is_fav=True).exists())
        self.assertFalse(Favourite.objects.filter(user=other_user, song=song, is_fav=True).exists())

    def test_anonymous_playlist_pages_require_login(self):
        song = self._create_song()
        before = self._counts()

        responses = [
            self.client.get(reverse('playlist')),
            self.client.get(reverse('playlist_songs', args=['Road Trip'])),
            self.client.post(reverse('playlist_songs', args=['Road Trip']), {'song_id': song.id}),
        ]

        for response in responses:
            with self.subTest(location=response.get('Location')):
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response['Location'])
        self.assertEqual(self._counts(), before)

    def test_detail_get_does_not_create_playlist(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Playlist.objects.count(), 0)

    def test_detail_create_playlist_is_idempotent(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)
        payload = {'playlist_action': 'create', 'playlist_name': 'Road Trip'}

        first_response = self.client.post(reverse('detail', args=[song.id]), payload)
        second_response = self.client.post(reverse('detail', args=[song.id]), payload)

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(
            Playlist.objects.filter(user=user, song=song, playlist_name='Road Trip').count(),
            1,
        )

    def test_detail_add_song_to_existing_playlist_is_idempotent(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        first_song = self._create_song(name='First Playlist Song')
        second_song = self._create_song(name='Second Playlist Song')
        Playlist.objects.create(user=user, song=first_song, playlist_name='Road Trip')
        self.client.force_login(user)
        payload = {'playlist_action': 'add', 'playlist_name': 'Road Trip'}

        first_response = self.client.post(reverse('detail', args=[second_song.id]), payload)
        second_response = self.client.post(reverse('detail', args=[second_song.id]), payload)

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(Playlist.objects.filter(user=user, playlist_name='Road Trip').count(), 2)
        self.assertEqual(
            Playlist.objects.filter(user=user, song=second_song, playlist_name='Road Trip').count(),
            1,
        )

    def test_detail_playlist_action_requires_valid_name_and_action(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        for payload in [
            {'playlist_action': 'create', 'playlist_name': ''},
            {'playlist_action': 'add', 'playlist_name': '   '},
            {'playlist_action': 'rename', 'playlist_name': 'Road Trip'},
        ]:
            with self.subTest(payload=payload):
                before = Playlist.objects.count()
                response = self.client.post(reverse('detail', args=[song.id]), payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(Playlist.objects.count(), before)

    def test_detail_playlist_name_rejects_overlong_value(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        max_length = Playlist._meta.get_field('playlist_name').max_length
        self.client.force_login(user)
        before = Playlist.objects.count()

        response = self.client.post(
            reverse('detail', args=[song.id]),
            {'playlist_action': 'create', 'playlist_name': 'x' * (max_length + 1)},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Playlist.objects.count(), before)

    def test_detail_playlist_invalid_song_id_does_not_create_playlist(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        self.client.force_login(user)

        response = self.client.post(
            reverse('detail', args=[999]),
            {'playlist_action': 'create', 'playlist_name': 'Road Trip'},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Playlist.objects.count(), 0)

    def test_playlist_page_lists_distinct_current_user_playlists(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        first_song = self._create_song(name='First Playlist Song')
        second_song = self._create_song(name='Second Playlist Song')
        other_song = self._create_song(name='Other Playlist Song')
        Playlist.objects.create(user=owner, song=first_song, playlist_name='Road Trip')
        Playlist.objects.create(user=owner, song=second_song, playlist_name='Road Trip')
        Playlist.objects.create(user=other_user, song=other_song, playlist_name='Other Mix')
        self.client.force_login(owner)

        response = self.client.get(reverse('playlist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Road Trip', count=1)
        self.assertNotContains(response, 'Other Mix')

    def test_playlist_songs_page_is_user_scoped(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        owner_song = self._create_song(name='Owner Playlist Song')
        other_song = self._create_song(name='Other Playlist Song')
        Playlist.objects.create(user=owner, song=owner_song, playlist_name='Shared Name')
        Playlist.objects.create(user=other_user, song=other_song, playlist_name='Other Name')
        self.client.force_login(owner)

        own_response = self.client.get(reverse('playlist_songs', args=['Shared Name']))
        other_response = self.client.get(reverse('playlist_songs', args=['Other Name']))

        self.assertEqual(own_response.status_code, 200)
        self.assertContains(own_response, 'Owner Playlist Song')
        self.assertNotContains(own_response, 'Other Playlist Song')
        self.assertEqual(other_response.status_code, 404)

    def test_playlist_songs_missing_media_renders_fallbacks(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = Song.objects.create(
            name='Blank Playlist Song',
            album='Recovery Album',
            language='English',
            year=2026,
            singer='Test Singer',
        )
        Playlist.objects.create(user=user, song=song, playlist_name='Road Trip')
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('playlist_songs', args=['Road Trip']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cover unavailable')
        self.assertContains(response, 'Audio unavailable.')
        self.assertEqual(self._counts(), before)

    def test_playlist_remove_requires_valid_song_id(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        Playlist.objects.create(user=user, song=song, playlist_name='Road Trip')
        self.client.force_login(user)

        for payload, expected_status in [
            ({}, 400),
            ({'song_id': 'abc'}, 400),
            ({'song_id': '999'}, 404),
        ]:
            with self.subTest(payload=payload):
                before = Playlist.objects.count()
                response = self.client.post(reverse('playlist_songs', args=['Road Trip']), payload)
                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(Playlist.objects.count(), before)

    def test_playlist_remove_is_scoped_to_current_user(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        song = self._create_song()
        Playlist.objects.create(user=owner, song=song, playlist_name='Shared Name')
        Playlist.objects.create(user=other_user, song=song, playlist_name='Shared Name')
        self.client.force_login(owner)

        response = self.client.post(reverse('playlist_songs', args=['Shared Name']), {'song_id': song.id})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Playlist.objects.filter(user=owner, song=song, playlist_name='Shared Name').exists())
        self.assertTrue(Playlist.objects.filter(user=other_user, song=song, playlist_name='Shared Name').exists())

    def test_anonymous_playback_routes_require_login(self):
        song = self._create_song()
        before = self._counts()

        routes = [
            reverse('play_song', args=[song.id]),
            reverse('play_song_index', args=[song.id]),
            reverse('play_recent_song', args=[song.id]),
        ]

        for url in routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response['Location'])
                self.assertEqual(self._counts(), before)

    def test_playback_invalid_song_id_returns_404_without_history_mutation(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        self.client.force_login(user)

        routes = [
            reverse('play_song', args=[999]),
            reverse('play_song_index', args=[999]),
            reverse('play_recent_song', args=[999]),
        ]

        for url in routes:
            with self.subTest(url=url):
                before = self._counts()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(self._counts(), before)

    def test_playback_routes_record_recent_for_current_user(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        response = self.client.get(reverse('play_song', args=[song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Recent.objects.filter(user=user, song=song).count(), 1)

    def test_repeated_playback_moves_song_to_newest_without_duplicates(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        first_song = self._create_song(name='First Recent Song')
        second_song = self._create_song(name='Second Recent Song')
        self.client.force_login(user)

        self.client.get(reverse('play_song', args=[first_song.id]))
        self.client.get(reverse('play_song', args=[second_song.id]))
        self.client.get(reverse('play_song', args=[first_song.id]))

        rows = list(Recent.objects.filter(user=user).order_by('-id'))
        self.assertEqual([row.song for row in rows], [first_song, second_song])
        self.assertEqual(Recent.objects.filter(user=user, song=first_song).count(), 1)

    def test_playback_history_is_scoped_to_current_user(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        song = self._create_song()
        Recent.objects.create(user=other_user, song=song)
        self.client.force_login(owner)

        response = self.client.get(reverse('play_song_index', args=[song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Recent.objects.filter(user=owner, song=song).count(), 1)
        self.assertEqual(Recent.objects.filter(user=other_user, song=song).count(), 1)

    def test_detail_get_does_not_create_recent_history(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._counts(), before)

    def test_recent_page_collapses_duplicate_history_in_newest_order(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        first_song = self._create_song(name='First Recent Song')
        second_song = self._create_song(name='Second Recent Song')
        Recent.objects.create(user=user, song=first_song)
        Recent.objects.create(user=user, song=second_song)
        Recent.objects.create(user=user, song=first_song)
        self.client.force_login(user)

        response = self.client.get(reverse('recent'))
        content = response.content.decode()
        first_play_url = reverse('play_recent_song', args=[first_song.id])
        second_play_url = reverse('play_recent_song', args=[second_song.id])

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, first_play_url, count=1)
        self.assertContains(response, second_play_url, count=1)
        self.assertLess(content.index(first_play_url), content.index(second_play_url))

    def test_recent_search_filters_current_user_history_without_mutation(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        matching_song = self._create_song(name='Blue Search Match')
        non_matching_song = self._create_song(name='Quiet Nonmatch')
        other_user_song = self._create_song(name='Blue Other User Match')
        Recent.objects.create(user=user, song=non_matching_song)
        Recent.objects.create(user=user, song=matching_song)
        Recent.objects.create(user=other_user, song=other_user_song)
        self.client.force_login(user)
        before_count = Recent.objects.count()
        before_order = list(Recent.objects.values_list('id', 'user_id', 'song_id').order_by('-id'))

        response = self.client.get(reverse('recent'), {'q': 'Blue'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Blue Search Match')
        self.assertNotContains(response, 'Quiet Nonmatch')
        self.assertNotContains(response, 'Blue Other User Match')
        self.assertEqual(Recent.objects.count(), before_count)
        self.assertEqual(
            list(Recent.objects.values_list('id', 'user_id', 'song_id').order_by('-id')),
            before_order,
        )

    def test_recent_page_missing_media_renders_fallbacks(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        song = Song.objects.create(
            name='Blank Recent Song',
            album='Recovery Album',
            language='English',
            year=2026,
            singer='Test Singer',
        )
        Recent.objects.create(user=user, song=song)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('recent'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cover unavailable')
        self.assertContains(response, 'Audio unavailable.')
        self.assertEqual(self._counts(), before)

    def test_blank_media_song_renders_safely_on_public_song_pages(self):
        self._create_song_with_media_state('Blank Hindi Public Song', language='Hindi')
        self._create_song_with_media_state('Blank English Public Song', language='English')

        for url in [
            reverse('index'),
            reverse('all_songs'),
            reverse('hindi_songs'),
            reverse('english_songs'),
        ]:
            with self.subTest(url=url):
                before = self._counts()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Cover unavailable')
                self.assertEqual(self._counts(), before)

    def test_public_search_pages_ignore_missing_q_without_error(self):
        self._create_song_with_media_state('Search Edge Song', language='English')

        for url in [reverse('index'), reverse('all_songs')]:
            with self.subTest(url=url):
                before = self._counts()
                response = self.client.get(url, {'cachebust': 'manual-qa'})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Search Edge Song')
                self.assertEqual(self._counts(), before)

    def test_blank_media_song_renders_safely_on_recent_page(self):
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        song = self._create_song_with_media_state('Blank Recent Media Song')
        Recent.objects.create(user=user, song=song)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('recent'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cover unavailable')
        self.assertContains(response, 'Audio unavailable.')
        self.assertEqual(self._counts(), before)

    def test_blank_media_song_renders_safely_on_detail_page(self):
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        song = self._create_song_with_media_state('Blank Detail Media Song')
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cover unavailable')
        self.assertContains(response, 'Audio unavailable.')
        self.assertEqual(self._counts(), before)

    def test_blank_media_song_renders_safely_on_favourite_page(self):
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        song = self._create_song_with_media_state('Blank Favourite Media Song')
        Favourite.objects.create(user=user, song=song, is_fav=True)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('favourite'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Audio unavailable.')
        self.assertEqual(self._counts(), before)

    def test_blank_media_song_renders_safely_on_playlist_songs_page(self):
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        song = self._create_song_with_media_state('Blank Playlist Media Song')
        Playlist.objects.create(user=user, song=song, playlist_name='Media Mix')
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('playlist_songs', args=['Media Mix']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cover unavailable')
        self.assertContains(response, 'Audio unavailable.')
        self.assertEqual(self._counts(), before)

    def test_image_only_song_renders_cover_and_audio_fallback(self):
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        song = self._create_song_with_media_state('Image Only Song', with_image=True)
        self.client.force_login(user)

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'image-only-song.jpg')
        self.assertContains(response, 'Audio unavailable.')

    def test_audio_only_song_renders_cover_fallback_and_audio_player(self):
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        song = self._create_song_with_media_state('Audio Only Song', with_audio=True)
        self.client.force_login(user)

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cover unavailable')
        self.assertContains(response, 'audio-only-song.mp3')

    def test_song_with_both_media_preserves_existing_rendering(self):
        song = self._create_song_with_media_state('Complete Media Song', with_image=True, with_audio=True)
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        Favourite.objects.create(user=user, song=song, is_fav=True)
        self.client.force_login(user)

        detail_response = self.client.get(reverse('detail', args=[song.id]))
        favourite_response = self.client.get(reverse('favourite'))

        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'complete-media-song.jpg')
        self.assertContains(detail_response, 'complete-media-song.mp3')
        self.assertNotContains(detail_response, 'Cover unavailable')
        self.assertNotContains(detail_response, 'Audio unavailable.')
        self.assertEqual(favourite_response.status_code, 200)
        self.assertContains(favourite_response, 'complete-media-song.mp3')

    def test_media_protected_pages_still_enforce_authentication(self):
        song = self._create_song_with_media_state('Protected Media Song')

        for url in [
            reverse('detail', args=[song.id]),
            reverse('favourite'),
            reverse('playlist'),
            reverse('playlist_songs', args=['Media Mix']),
        ]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response['Location'])

    def test_recovery_smoke_harness_command_passes_and_reports_totals(self):
        with transaction.atomic():
            results = run_smoke_checks()
            report = render_report(results)
            transaction.set_rollback(True)

        self.assertIn('PASS', report)
        self.assertIn('Total checks:', report)
        self.assertIn('Failed checks: 0', report)
        self.assertIn('Overall result: PASS', report)
        self.assertIn('legacy navigation design', report)
        self.assertTrue(all(result['passed'] for result in results))

    def test_recovery_smoke_harness_detects_wrong_expectation(self):
        with transaction.atomic():
            results = run_smoke_checks(expect_overrides={'public:index': 404})
            transaction.set_rollback(True)

        report = render_report(results)
        self.assertIn('FAIL', report)
        self.assertTrue(any(not result['passed'] for result in results))

    def test_recovery_smoke_harness_leaves_row_counts_unchanged(self):
        before = self._counts()
        before['users'] = User.objects.count()

        with transaction.atomic():
            results = run_smoke_checks()
            transaction.set_rollback(True)

        after = self._counts()
        after['users'] = User.objects.count()
        self.assertTrue(all(result['passed'] for result in results))
        self.assertEqual(after, before)

    def test_seed_demo_data_creates_fictional_catalog_without_media(self):
        output = StringIO()

        call_command('seed_demo_data', stdout=output)

        demo_songs = Song.objects.filter(album=DEMO_ALBUM).order_by('name')
        self.assertEqual(demo_songs.count(), len(DEMO_SONGS))
        self.assertIn('8 created, 0 updated, 0 unchanged', output.getvalue())
        self.assertTrue(demo_songs.filter(language='Hindi').exists())
        self.assertTrue(demo_songs.filter(language='English').exists())
        for song in demo_songs:
            self.assertEqual(song.song_img.name, '')
            self.assertEqual(song.song_file.name, '')

    def test_seed_demo_data_is_idempotent(self):
        first_output = StringIO()
        second_output = StringIO()

        call_command('seed_demo_data', stdout=first_output)
        before_ids = list(Song.objects.filter(album=DEMO_ALBUM).values_list('id', flat=True).order_by('id'))
        call_command('seed_demo_data', stdout=second_output)

        self.assertEqual(Song.objects.filter(album=DEMO_ALBUM).count(), len(DEMO_SONGS))
        self.assertEqual(
            list(Song.objects.filter(album=DEMO_ALBUM).values_list('id', flat=True).order_by('id')),
            before_ids,
        )
        self.assertIn('0 created, 0 updated, 8 unchanged', second_output.getvalue())

    def test_seed_demo_data_populates_language_pages(self):
        call_command('seed_demo_data', stdout=StringIO())

        hindi_response = self.client.get(reverse('hindi_songs'))
        english_response = self.client.get(reverse('english_songs'))

        self.assertEqual(hindi_response.status_code, 200)
        self.assertEqual(english_response.status_code, 200)
        self.assertContains(hindi_response, 'Dil Ki Dhoop')
        self.assertContains(english_response, 'Crimson Echo')
        self.assertContains(hindi_response, 'Cover unavailable')
        self.assertContains(english_response, 'Cover unavailable')

    def test_seed_demo_data_clear_removes_only_demo_rows(self):
        retained_song = self._create_song(name='Personal Song')
        call_command('seed_demo_data', stdout=StringIO())

        call_command('seed_demo_data', '--clear', stdout=StringIO())

        self.assertFalse(Song.objects.filter(album=DEMO_ALBUM).exists())
        self.assertTrue(Song.objects.filter(id=retained_song.id).exists())
