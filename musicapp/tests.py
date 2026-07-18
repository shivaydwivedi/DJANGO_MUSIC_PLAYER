import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

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

    def test_anonymous_public_pages_render_with_empty_library(self):
        routes = [
            (reverse('index'), 'No songs available yet.'),
            (reverse('all_songs'), 'No songs available yet.'),
            (reverse('hindi_songs'), 'No Hindi songs available yet.'),
            (reverse('english_songs'), 'No English songs available yet.'),
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
