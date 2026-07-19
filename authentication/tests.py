from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.test import TestCase, override_settings
from django.urls import get_resolver, reverse
from importlib import import_module

from .compat import get_safe_redirect_url
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
            reverse('profile'),
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

    def test_anonymous_profile_redirects_to_login(self):
        response = self.client.get(reverse('profile'))

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
        self.assertNotContains(response, 'Profile')

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

    def test_same_host_absolute_next_redirect_is_honored(self):
        user = self._create_user()

        response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'secret-pass',
            'next': 'http://testserver{0}'.format(reverse('mymusic')),
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver{0}'.format(reverse('mymusic')))

    def test_protocol_relative_external_next_redirect_is_rejected(self):
        user = self._create_user()

        response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'secret-pass',
            'next': '//example.invalid/steal',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_malformed_next_redirect_is_rejected(self):
        user = self._create_user()

        response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'secret-pass',
            'next': 'http://[::1',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_missing_next_redirect_uses_default(self):
        user = self._create_user()

        response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'secret-pass',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_secure_request_rejects_http_same_host_next_redirect(self):
        user = self._create_user()

        response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'secret-pass',
            'next': 'http://testserver{0}'.format(reverse('mymusic')),
        }, secure=True)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('index'))

    def test_redirect_compat_helper_accepts_relative_internal_url(self):
        request = RequestFactory().get(reverse('login'), {'next': reverse('mymusic')})

        self.assertEqual(get_safe_redirect_url(request), reverse('mymusic'))

    def test_redirect_compat_helper_rejects_external_url(self):
        request = RequestFactory().get(reverse('login'), {'next': 'https://example.invalid/steal'})

        self.assertIsNone(get_safe_redirect_url(request))

    def test_redirect_compat_helper_rejects_protocol_relative_external_url(self):
        request = RequestFactory().get(reverse('login'), {'next': '//example.invalid/steal'})

        self.assertIsNone(get_safe_redirect_url(request))

    def test_redirect_compat_helper_rejects_malformed_url(self):
        request = RequestFactory().get(reverse('login'), {'next': 'http://[::1'})

        self.assertIsNone(get_safe_redirect_url(request))

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

    def test_profile_returns_200_and_displays_current_user_identity(self):
        user = self._create_user(username='profile-listener', email='profile@example.com')
        self.client.force_login(user)
        User.objects.filter(pk=user.pk).update(last_login=None)

        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'profile-listener')
        self.assertContains(response, 'profile@example.com')
        self.assertContains(response, 'Sonica account')
        self.assertContains(response, 'No login recorded yet')
        self.assertNotContains(response, 'password')

    def test_profile_handles_missing_email(self):
        user = self._create_user(username='missing-email', email='')
        self.client.force_login(user)

        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No email added')

    def test_profile_does_not_expose_another_users_data(self):
        owner = self._create_user(username='owner', email='owner@example.com')
        other_user = self._create_user(username='other-profile', email='other@example.com')
        song = self._create_song(name='Other User Recent Song')
        Favourite.objects.create(user=other_user, song=song, is_fav=True)
        Playlist.objects.create(user=other_user, song=song, playlist_name='Other Secret Mix')
        Recent.objects.create(user=other_user, song=song)
        self.client.force_login(owner)

        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'owner@example.com')
        self.assertNotContains(response, 'other-profile')
        self.assertNotContains(response, 'other@example.com')
        self.assertNotContains(response, 'Other User Recent Song')
        self.assertNotContains(response, 'Other Secret Mix')

    def test_profile_statistics_are_user_scoped(self):
        owner = self._create_user(username='stats-owner', email='stats-owner@example.com')
        other_user = self._create_user(username='stats-other', email='stats-other@example.com')
        first_song = self._create_song(name='Owner First Song')
        second_song = self._create_song(name='Owner Second Song')
        other_song = self._create_song(name='Other Stats Song')
        Favourite.objects.create(user=owner, song=first_song, is_fav=True)
        Favourite.objects.create(user=other_user, song=other_song, is_fav=True)
        Playlist.objects.create(user=owner, song=first_song, playlist_name='Focus Mix')
        Playlist.objects.create(user=owner, song=second_song, playlist_name='Focus Mix')
        Playlist.objects.create(user=other_user, song=other_song, playlist_name='Other Mix')
        Recent.objects.create(user=owner, song=first_song)
        Recent.objects.create(user=owner, song=second_song)
        Recent.objects.create(user=other_user, song=other_song)
        self.client.force_login(owner)

        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Favourite songs')
        self.assertContains(response, 'Distinct playlists')
        self.assertContains(response, 'Recent plays')
        self.assertContains(response, 'Playlist song saves')
        self.assertContains(response, '<span class="profile-stat-value">1</span>', count=2, html=True)
        self.assertContains(response, '<span class="profile-stat-value">2</span>', count=2, html=True)
        self.assertNotContains(response, 'Other Stats Song')

    def test_profile_recent_activity_is_newest_first_and_limited(self):
        user = self._create_user(username='recent-owner', email='recent-owner@example.com')
        songs = [self._create_song(name='Recent Song {0}'.format(index)) for index in range(7)]
        for song in songs:
            Recent.objects.create(user=user, song=song)
        self.client.force_login(user)

        response = self.client.get(reverse('profile'))
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recent Song 6')
        self.assertContains(response, 'Recent Song 2')
        self.assertNotContains(response, 'Recent Song 1')
        self.assertNotContains(response, 'Recent Song 0')
        self.assertLess(content.index('Recent Song 6'), content.index('Recent Song 5'))
        self.assertLess(content.index('Recent Song 5'), content.index('Recent Song 4'))

    def test_profile_empty_statistics_render(self):
        user = self._create_user(username='empty-profile', email='empty-profile@example.com')
        self.client.force_login(user)

        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="profile-stat-value">0</span>', count=4, html=True)
        self.assertContains(response, 'No recent listening activity yet.')

    def test_profile_update_succeeds_for_current_user(self):
        user = self._create_user(username='old-name', email='old@example.com')
        self.client.force_login(user)

        response = self.client.post(reverse('profile'), {
            'username': '  new-name  ',
            'email': '  new@example.com  ',
        })
        user.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('profile'))
        self.assertEqual(user.username, 'new-name')
        self.assertEqual(user.email, 'new@example.com')

    def test_profile_update_rejects_duplicate_username(self):
        self._create_user(username='taken-name', email='taken-name@example.com')
        user = self._create_user(username='current-name', email='current@example.com')
        self.client.force_login(user)

        response = self.client.post(reverse('profile'), {
            'username': 'Taken-Name',
            'email': 'current@example.com',
        })
        user.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that username already exists.')
        self.assertEqual(user.username, 'current-name')

    def test_profile_update_rejects_duplicate_email(self):
        self._create_user(username='email-owner', email='taken@example.com')
        user = self._create_user(username='current-email', email='current@example.com')
        self.client.force_login(user)

        response = self.client.post(reverse('profile'), {
            'username': 'current-email',
            'email': 'TAKEN@example.com',
        })
        user.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that email already exists.')
        self.assertEqual(user.email, 'current@example.com')

    def test_profile_update_cannot_affect_another_user(self):
        owner = self._create_user(username='owner-before', email='owner-before@example.com')
        other_user = self._create_user(username='other-before', email='other-before@example.com')
        self.client.force_login(owner)

        response = self.client.post(reverse('profile'), {
            'username': 'owner-after',
            'email': 'owner-after@example.com',
        })
        owner.refresh_from_db()
        other_user.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(owner.username, 'owner-after')
        self.assertEqual(owner.email, 'owner-after@example.com')
        self.assertEqual(other_user.username, 'other-before')
        self.assertEqual(other_user.email, 'other-before@example.com')

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

    def test_navigation_shows_profile_only_when_authenticated(self):
        anonymous_response = self.client.get(reverse('index'))
        user = self._create_user(username='nav-user', email='nav@example.com')
        self.client.force_login(user)
        authenticated_response = self.client.get(reverse('index'))
        profile_response = self.client.get(reverse('profile'))

        self.assertEqual(anonymous_response.status_code, 200)
        self.assertNotContains(anonymous_response, reverse('profile'))
        self.assertEqual(authenticated_response.status_code, 200)
        self.assertContains(authenticated_response, reverse('profile'))
        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, 'aria-current="page"')

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

    def test_settings_module_imports_successfully(self):
        settings_module = import_module('musicplayer.settings')

        self.assertEqual(settings_module.ROOT_URLCONF, 'musicplayer.urls')
        self.assertIn('allauth', settings_module.INSTALLED_APPS)

    def test_project_url_configuration_imports_successfully(self):
        resolver = get_resolver()

        self.assertTrue(any(pattern.pattern._route == 'accounts/' for pattern in resolver.url_patterns))
        self.assertTrue(any(pattern.pattern._route == 'authentication/' for pattern in resolver.url_patterns))

    def test_allauth_urls_remain_mounted_at_accounts_only(self):
        resolver = get_resolver()
        allauth_mounts = [
            pattern.pattern._route
            for pattern in resolver.url_patterns
            if getattr(getattr(pattern, 'urlconf_name', None), '__name__', None) == 'allauth.urls'
        ]

        self.assertEqual(allauth_mounts, ['accounts/'])

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
