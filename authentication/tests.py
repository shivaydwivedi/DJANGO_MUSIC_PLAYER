from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from musicapp.models import Favourite, Playlist, Recent, Song


class AuthenticationFlowTests(TestCase):
    def _create_user(self, username='listener', email='listener@example.com'):
        return User.objects.create_user(
            username=username,
            email=email,
            password='secret-pass',
        )

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

    def _signup_payload(self, username='new-listener', email='new-listener@example.com'):
        return {
            'username': username,
            'email': email,
            'password1': 'complex-secret-pass',
            'password2': 'complex-secret-pass',
        }

    def test_anonymous_mymusic_redirects_to_login(self):
        response = self.client.get(reverse('mymusic'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_authenticated_mymusic_returns_200_without_mutation(self):
        user = self._create_user()
        self.client.force_login(user)
        before = {
            'users': User.objects.count(),
            'songs': Song.objects.count(),
            'recent': Recent.objects.count(),
            'favourites': Favourite.objects.count(),
            'playlists': Playlist.objects.count(),
        }

        response = self.client.get(reverse('mymusic'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            'users': User.objects.count(),
            'songs': Song.objects.count(),
            'recent': Recent.objects.count(),
            'favourites': Favourite.objects.count(),
            'playlists': Playlist.objects.count(),
        }, before)

    def test_existing_protected_pages_still_require_login(self):
        song = self._create_song()
        protected_urls = [
            reverse('favourite'),
            reverse('playlist'),
            reverse('playlist_songs', args=['Road Trip']),
            reverse('play_song', args=[song.id]),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response['Location'])

    def test_valid_login_succeeds_and_redirects_to_index(self):
        user = self._create_user()

        response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'secret-pass',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertTrue(get_user(self.client).is_authenticated)

    def test_login_page_hides_google_auth_when_unconfigured(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in to Sonica')
        self.assertContains(response, 'Log In')
        self.assertNotContains(response, 'Sign in with Google')

    @override_settings(ENABLE_GOOGLE_AUTH=True)
    def test_login_page_does_not_render_google_auth_without_social_app(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Sign in with Google')

    def test_invalid_login_does_not_authenticate(self):
        user = self._create_user()

        response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'wrong-pass',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user(self.client).is_authenticated)
        self.assertContains(response, 'This user does not exist!')

    def test_signup_page_renders_local_form_without_google_auth(self):
        response = self.client.get(reverse('signup'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create your Sonica account')
        self.assertContains(response, 'Sign Up')
        self.assertNotContains(response, 'Sign up with Google')

    @override_settings(ENABLE_GOOGLE_AUTH=True)
    def test_signup_page_does_not_render_google_auth_without_social_app(self):
        response = self.client.get(reverse('signup'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Sign up with Google')

    def test_valid_local_next_redirect_is_honored(self):
        user = self._create_user()

        response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'secret-pass',
            'next': reverse('mymusic'),
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('mymusic'))

    def test_external_next_redirect_is_replaced_with_safe_redirect(self):
        user = self._create_user()

        response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'secret-pass',
            'next': 'https://example.invalid/steal',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_login_get_does_not_mutate_database(self):
        before = User.objects.count()

        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), before)

    def test_authenticated_login_get_redirects_safely(self):
        user = self._create_user()
        self.client.force_login(user)

        local_response = self.client.get(reverse('login'), {'next': reverse('mymusic')})
        external_response = self.client.get(reverse('login'), {'next': 'https://example.invalid/steal'})

        self.assertEqual(local_response.status_code, 302)
        self.assertEqual(local_response['Location'], reverse('mymusic'))
        self.assertEqual(external_response.status_code, 302)
        self.assertEqual(external_response['Location'], reverse('index'))

    def test_valid_signup_creates_one_user(self):
        response = self.client.post(reverse('signup'), self._signup_payload())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('login'))
        self.assertEqual(User.objects.filter(username='new-listener').count(), 1)
        self.assertEqual(User.objects.get(username='new-listener').email, 'new-listener@example.com')

    def test_invalid_signup_creates_no_user(self):
        before = User.objects.count()
        payload = self._signup_payload()
        payload['password2'] = 'different-pass'

        response = self.client.post(reverse('signup'), payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), before)

    def test_duplicate_username_is_rejected(self):
        self._create_user(username='taken', email='taken@example.com')
        before = User.objects.count()

        response = self.client.post(
            reverse('signup'),
            self._signup_payload(username='taken', email='unique@example.com'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), before)

    def test_duplicate_email_is_rejected(self):
        self._create_user(username='existing', email='taken@example.com')
        before = User.objects.count()

        response = self.client.post(
            reverse('signup'),
            self._signup_payload(username='unique', email='taken@example.com'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), before)

    def test_post_logout_clears_session(self):
        user = self._create_user()
        self.client.force_login(user)

        response = self.client.post(reverse('logout'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_anonymous_post_logout_is_safe(self):
        response = self.client.post(reverse('logout'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_get_logout_is_not_allowed_and_does_not_clear_session(self):
        user = self._create_user()
        self.client.force_login(user)

        response = self.client.get(reverse('logout'))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(get_user(self.client).is_authenticated)

    def test_logout_ignores_external_next_redirect(self):
        user = self._create_user()
        self.client.force_login(user)

        response = self.client.post(reverse('logout'), {'next': 'https://example.invalid/steal'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_public_browsing_pages_remain_anonymous_accessible(self):
        public_urls = [
            reverse('index'),
            reverse('all_songs'),
            reverse('hindi_songs'),
            reverse('english_songs'),
            reverse('recent'),
        ]

        for url in public_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_protected_page_does_not_expose_other_user_information(self):
        owner = self._create_user(username='owner', email='owner@example.com')
        other_user = self._create_user(username='other-user', email='other@example.com')
        song = self._create_song(name='Private Playlist Song')
        Playlist.objects.create(user=other_user, song=song, playlist_name='Other Private Mix')
        self.client.force_login(owner)

        response = self.client.get(reverse('mymusic'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Other Private Mix')
        self.assertNotContains(response, 'Private Playlist Song')
