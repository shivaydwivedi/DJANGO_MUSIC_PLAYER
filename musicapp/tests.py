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
        song = Song.objects.create(
            name='Synthetic Test Song',
            album='Recovery Album',
            language='English',
            song_img=SimpleUploadedFile('cover.jpg', b'cover-bytes', content_type='image/jpeg'),
            year=2026,
            singer='Test Singer',
            song_file=SimpleUploadedFile('song.mp3', b'audio-bytes', content_type='audio/mpeg'),
        )

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
