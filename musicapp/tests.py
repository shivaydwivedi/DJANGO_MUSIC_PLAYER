import os
import subprocess
import sys
import json
import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import Storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from musicapp.management.commands.seed_demo_catalog import DEMO_CATALOG_SONGS
from musicapp.management.commands.seed_demo_data import DEMO_ALBUM, DEMO_SONGS
from musicapp.management.commands.project_smoke_test import (
    render_report,
    run_smoke_checks,
)

from .models import Favourite, Playlist, PlaylistContainer, PlaylistSong, Recent, Song
from .validators import (
    ALLOWED_AUDIO_EXTENSIONS,
    ALLOWED_COVER_EXTENSIONS,
    DEFAULT_MAX_AUDIO_UPLOAD_SIZE,
    DEFAULT_MAX_COVER_UPLOAD_SIZE,
)


TEST_MEDIA_ROOT = tempfile.mkdtemp()
PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
            'playlist_containers': PlaylistContainer.objects.count(),
            'playlist_songs': PlaylistSong.objects.count(),
        }

    def _create_song(self, name='Synthetic Test Song'):
        return Song.objects.create(
            name=name,
            album='Test Album',
            language='English',
            song_img=SimpleUploadedFile('cover.jpg', b'cover-bytes', content_type='image/jpeg'),
            year=2026,
            singer='Test Singer',
            song_file=SimpleUploadedFile('song.mp3', b'audio-bytes', content_type='audio/mpeg'),
        )

    def _create_song_with_media_state(self, name, language='English', with_image=False, with_audio=False):
        kwargs = {
            'name': name,
            'album': 'Test Album',
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

    def _unsaved_song(self, name='Validation Song', song_img='', song_file=''):
        return Song(
            name=name,
            album='Validation Album',
            language='English',
            year=2026,
            singer='Validation Singer',
            song_img=song_img,
            song_file=song_file,
        )

    def _catalog_source(self, rows=None, audio_name='song.mp3', cover_name='cover.jpg'):
        source_dir = Path(tempfile.mkdtemp())
        manifest_path = source_dir / 'catalog.json'
        (source_dir / audio_name).write_bytes(b'audio-bytes')
        (source_dir / cover_name).write_bytes(b'cover-bytes')
        if rows is None:
            rows = [
                {
                    'name': 'Authorised Test Song',
                    'album': 'Authorised Test Album',
                    'language': 'English',
                    'year': 2026,
                    'singer': 'Authorised Artist',
                    'audio_filename': audio_name,
                    'cover_filename': cover_name,
                },
            ]
        manifest_path.write_text(json.dumps(rows), encoding='utf-8')
        return source_dir, manifest_path

    def _run_import(self, *args, **kwargs):
        output = kwargs.pop('stdout', StringIO())
        error = kwargs.pop('stderr', StringIO())
        call_command('import_song_catalog', *args, stdout=output, stderr=error, **kwargs)
        return output.getvalue(), error.getvalue()

    def _settings_probe(self, env_overrides, code):
        env = os.environ.copy()
        env.update(env_overrides)
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        return subprocess.run(
            [sys.executable, '-c', code],
            cwd=PROJECT_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_local_media_storage_uses_filesystem_when_cloudinary_url_is_absent(self):
        result = self._settings_probe(
            {'CLOUDINARY_URL': ''},
            (
                'import musicplayer.settings as settings; '
                'print(settings.STORAGES["default"]["BACKEND"]); '
                'print("cloudinary_storage" in settings.INSTALLED_APPS)'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                'django.core.files.storage.FileSystemStorage',
                'False',
            ],
        )

    def test_cloudinary_media_storage_is_selected_when_cloudinary_url_exists(self):
        result = self._settings_probe(
            {'CLOUDINARY_URL': 'cloudinary://demo_key:demo_secret@demo_cloud'},
            (
                'import django; django.setup(); '
                'import musicplayer.settings as settings; '
                'from django.apps import apps; '
                'from musicapp.models import Song; '
                'print(settings.USE_CLOUDINARY_MEDIA); '
                'print(settings.CONFIGURE_CLOUDINARY_FIELD_STORAGE); '
                'print(apps.get_app_config("musicapp").__class__.__name__); '
                'print(settings.STORAGES["default"]["BACKEND"]); '
                'print("cloudinary_storage" in settings.INSTALLED_APPS); '
                'print("cloudinary" in settings.INSTALLED_APPS); '
                'print(type(Song._meta.get_field("song_img").storage).__name__); '
                'print(type(Song._meta.get_field("song_file").storage).__name__); '
                'print(Song._meta.get_field("song_img").storage.url("media/cover_public_id")); '
                'print(Song._meta.get_field("song_file").storage.url("media/audio_public_id"))'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(
            lines[:8],
            [
                'True',
                'True',
                'MusicappConfig',
                'musicapp.storage.SonicaCloudinaryImageStorage',
                'True',
                'True',
                'SonicaCloudinaryImageStorage',
                'SonicaCloudinaryAudioStorage',
            ],
        )
        self.assertIn('/image/upload/', lines[8])
        self.assertIn('/video/upload/', lines[9])

    def test_whitenoise_static_storage_remains_independent_from_cloudinary_media(self):
        result = self._settings_probe(
            {
                'CLOUDINARY_URL': 'cloudinary://demo_key:demo_secret@demo_cloud',
                'DEBUG': 'False',
                'SECRET_KEY': 'production-settings-test-secret-value-with-enough-length-12345',
                'ALLOWED_HOSTS': 'example.com',
            },
            (
                'import musicplayer.settings as settings; '
                'print(settings.STORAGES["default"]["BACKEND"]); '
                'print(settings.STORAGES["staticfiles"]["BACKEND"]); '
                'print(settings.INSTALLED_APPS.index("django.contrib.staticfiles") '
                '< settings.INSTALLED_APPS.index("cloudinary_storage"))'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                'musicapp.storage.SonicaCloudinaryImageStorage',
                'whitenoise.storage.CompressedManifestStaticFilesStorage',
                'True',
            ],
        )

    def test_cloudinary_media_storage_upload_options_use_expected_resource_types(self):
        result = self._settings_probe(
            {'CLOUDINARY_URL': 'cloudinary://demo_key:demo_secret@demo_cloud'},
            (
                'import django; django.setup(); '
                'from django.core.files.base import ContentFile; '
                'from unittest.mock import patch; '
                'from musicapp.storage import SonicaCloudinaryAudioStorage, SonicaCloudinaryImageStorage; '
                'patcher = patch("cloudinary.uploader.upload", return_value={"public_id": "media/test"}); '
                'upload = patcher.start(); '
                'SonicaCloudinaryImageStorage()._save("cover.jpg", ContentFile(b"cover")); '
                'print(upload.call_args.kwargs["resource_type"]); '
                'upload.reset_mock(); '
                'SonicaCloudinaryAudioStorage()._save("track.mp3", ContentFile(b"audio")); '
                'print(upload.call_args.kwargs["resource_type"]); '
                'patcher.stop()'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['image', 'video'])

    def test_cloudinary_media_storage_urls_use_expected_resource_types(self):
        result = self._settings_probe(
            {'CLOUDINARY_URL': 'cloudinary://demo_key:demo_secret@demo_cloud'},
            (
                'import django; django.setup(); '
                'from musicapp.storage import SonicaCloudinaryAudioStorage, SonicaCloudinaryImageStorage; '
                'print(SonicaCloudinaryImageStorage().url("media/cover_public_id")); '
                'print(SonicaCloudinaryAudioStorage().url("media/audio_public_id"))'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        urls = result.stdout.splitlines()
        self.assertIn('/image/upload/', urls[0])
        self.assertIn('/video/upload/', urls[1])

    def test_test_environment_keeps_cloudinary_storage_disabled(self):
        self.assertFalse(settings.USE_CLOUDINARY_MEDIA)
        self.assertNotIn('cloudinary_storage', settings.INSTALLED_APPS)
        self.assertEqual(
            settings.STORAGES['default']['BACKEND'],
            'django.core.files.storage.FileSystemStorage',
        )

    def test_song_upload_validation_accepts_supported_audio_extensions(self):
        for extension in sorted(ALLOWED_AUDIO_EXTENSIONS):
            with self.subTest(extension=extension):
                song = self._unsaved_song(
                    song_file=SimpleUploadedFile(
                        'track{0}'.format(extension),
                        b'audio-bytes',
                        content_type='application/octet-stream',
                    )
                )
                song.full_clean()

    def test_song_upload_validation_rejects_unsupported_audio_extensions(self):
        for filename in ['track.exe', 'track.mp3.exe', 'track.txt']:
            with self.subTest(filename=filename):
                song = self._unsaved_song(
                    song_file=SimpleUploadedFile(
                        filename,
                        b'audio-bytes',
                        content_type='audio/mpeg',
                    )
                )
                with self.assertRaisesMessage(ValidationError, 'Song audio must use one of these file extensions'):
                    song.full_clean()

    def test_song_upload_validation_accepts_supported_cover_extensions(self):
        for extension in sorted(ALLOWED_COVER_EXTENSIONS):
            with self.subTest(extension=extension):
                song = self._unsaved_song(
                    song_img=SimpleUploadedFile(
                        'cover{0}'.format(extension),
                        b'cover-bytes',
                        content_type='application/octet-stream',
                    )
                )
                song.full_clean()

    def test_song_upload_validation_rejects_unsupported_cover_extensions(self):
        for filename in ['cover.svg', 'cover.jpg.exe', 'cover.gif']:
            with self.subTest(filename=filename):
                song = self._unsaved_song(
                    song_img=SimpleUploadedFile(
                        filename,
                        b'cover-bytes',
                        content_type='image/jpeg',
                    )
                )
                with self.assertRaisesMessage(ValidationError, 'Song cover must use one of these file extensions'):
                    song.full_clean()

    def test_song_upload_validation_still_accepts_valid_cover_and_audio_together(self):
        song = self._unsaved_song(
            song_img=SimpleUploadedFile('cover.webp', b'cover-bytes', content_type='image/webp'),
            song_file=SimpleUploadedFile('track.m4a', b'audio-bytes', content_type='audio/mp4'),
        )

        song.full_clean()

    def test_song_upload_validation_still_rejects_invalid_cover_and_audio(self):
        cases = [
            (
                self._unsaved_song(
                    song_img=SimpleUploadedFile('cover.svg', b'cover-bytes', content_type='image/svg+xml'),
                    song_file=SimpleUploadedFile('track.mp3', b'audio-bytes', content_type='audio/mpeg'),
                ),
                'Song cover must use one of these file extensions',
            ),
            (
                self._unsaved_song(
                    song_img=SimpleUploadedFile('cover.jpg', b'cover-bytes', content_type='image/jpeg'),
                    song_file=SimpleUploadedFile('track.exe', b'audio-bytes', content_type='audio/mpeg'),
                ),
                'Song audio must use one of these file extensions',
            ),
        ]

        for song, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                with self.assertRaisesMessage(ValidationError, expected_error):
                    song.full_clean()

    @override_settings(SONICA_MAX_AUDIO_UPLOAD_SIZE=4)
    def test_song_upload_validation_rejects_audio_over_configured_size_limit(self):
        song = self._unsaved_song(
            song_file=SimpleUploadedFile('track.mp3', b'12345', content_type='audio/mpeg')
        )

        with self.assertRaisesMessage(ValidationError, 'Song audio must be'):
            song.full_clean()

    @override_settings(SONICA_MAX_COVER_UPLOAD_SIZE=4)
    def test_song_upload_validation_rejects_cover_over_configured_size_limit(self):
        song = self._unsaved_song(
            song_img=SimpleUploadedFile('cover.jpg', b'12345', content_type='image/jpeg')
        )

        with self.assertRaisesMessage(ValidationError, 'Song cover must be'):
            song.full_clean()

    def test_song_upload_validation_allows_blank_existing_media_fields(self):
        song = self._unsaved_song(song_img='', song_file='')

        song.full_clean()

    def test_existing_committed_extensionless_cover_allows_metadata_update(self):
        song = Song.objects.create(
            name='Cloudinary Cover Song',
            album='Original Album',
            language='English',
            year=2026,
            singer='Cloudinary Artist',
            song_img='media/my__aonpi6',
        )

        song.refresh_from_db()
        song.album = 'Updated Album'

        song.full_clean()

    def test_existing_committed_extensionless_cover_allows_new_audio_upload(self):
        song = Song.objects.create(
            name='Cloudinary Cover Audio Song',
            album='Original Album',
            language='English',
            year=2026,
            singer='Cloudinary Artist',
            song_img='media/my__aonpi6',
        )

        song.refresh_from_db()
        song.song_file = SimpleUploadedFile('new-audio.mp3', b'audio-bytes', content_type='audio/mpeg')

        song.full_clean()

    def test_existing_committed_extensionless_audio_allows_new_cover_upload(self):
        song = Song.objects.create(
            name='Cloudinary Audio Cover Song',
            album='Original Album',
            language='English',
            year=2026,
            singer='Cloudinary Artist',
            song_file='media/audio__x9k2q',
        )

        song.refresh_from_db()
        song.song_img = SimpleUploadedFile('new-cover.webp', b'cover-bytes', content_type='image/webp')

        song.full_clean()

    def test_existing_committed_local_filesystem_media_remains_valid(self):
        song = Song.objects.create(
            name='Local Filesystem Song',
            album='Original Album',
            language='English',
            year=2026,
            singer='Local Artist',
            song_img='local-cover.jpg',
            song_file='local-audio.mp3',
        )

        song.refresh_from_db()
        song.year = 2027

        song.full_clean()

    def test_song_modelform_applies_upload_validation(self):
        SongForm = forms.modelform_factory(
            Song,
            fields=['name', 'album', 'language', 'song_img', 'year', 'singer', 'song_file'],
        )
        form = SongForm(
            data={
                'name': 'Form Validation Song',
                'album': 'Validation Album',
                'language': 'English',
                'year': 2026,
                'singer': 'Validation Singer',
            },
            files={
                'song_img': SimpleUploadedFile('cover.png', b'cover-bytes', content_type='image/png'),
                'song_file': SimpleUploadedFile('track.exe', b'audio-bytes', content_type='audio/mpeg'),
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn('Song audio must use one of these file extensions', str(form.errors))

    def test_import_song_catalog_requires_source_for_import(self):
        with self.assertRaisesMessage(CommandError, '--source and --manifest are required for import'):
            call_command('import_song_catalog')

    def test_import_song_catalog_requires_manifest_for_import(self):
        source_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        with self.assertRaisesMessage(CommandError, '--manifest is required for import'):
            call_command('import_song_catalog', '--source', str(source_dir))

    def test_import_song_catalog_rejects_invalid_manifest(self):
        source_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)
        manifest_path = source_dir / 'catalog.json'
        manifest_path.write_text('{invalid', encoding='utf-8')

        with self.assertRaisesMessage(CommandError, 'Manifest JSON is invalid'):
            call_command('import_song_catalog', '--source', str(source_dir), '--manifest', str(manifest_path), '--dry-run')

    def test_import_song_catalog_rejects_missing_files(self):
        source_dir, manifest_path = self._catalog_source(rows=[
            {
                'name': 'Missing File Song',
                'album': 'Authorised Test Album',
                'language': 'English',
                'year': 2026,
                'singer': 'Authorised Artist',
                'audio_filename': 'missing.mp3',
                'cover_filename': 'cover.jpg',
            },
        ])
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        with self.assertRaisesMessage(CommandError, 'audio file not found'):
            call_command('import_song_catalog', '--source', str(source_dir), '--manifest', str(manifest_path), '--dry-run')

    def test_import_song_catalog_rejects_unsupported_extension(self):
        source_dir, manifest_path = self._catalog_source(audio_name='song.exe')
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        with self.assertRaisesMessage(CommandError, 'Song audio must use one of these file extensions'):
            call_command('import_song_catalog', '--source', str(source_dir), '--manifest', str(manifest_path), '--dry-run')

    def test_import_song_catalog_dry_run_performs_no_writes(self):
        source_dir, manifest_path = self._catalog_source()
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        output, _ = self._run_import('--source', str(source_dir), '--manifest', str(manifest_path), '--dry-run')

        self.assertEqual(Song.objects.count(), 0)
        self.assertIn('WOULD CREATE: Authorised Test Song - Authorised Artist', output)
        self.assertIn('Dry run complete: 1 create, 0 update, 0 skip, 0 failed.', output)

    def test_import_song_catalog_requires_rights_confirmation_for_real_import(self):
        source_dir, manifest_path = self._catalog_source()
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        with self.assertRaisesMessage(CommandError, 'Real imports require --confirm-rights'):
            call_command('import_song_catalog', '--source', str(source_dir), '--manifest', str(manifest_path))

    def test_import_song_catalog_valid_import_creates_song(self):
        source_dir, manifest_path = self._catalog_source()
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        output, _ = self._run_import(
            '--source',
            str(source_dir),
            '--manifest',
            str(manifest_path),
            '--confirm-rights',
        )

        song = Song.objects.get(name='Authorised Test Song', singer='Authorised Artist')
        self.assertEqual(song.album, 'Authorised Test Album')
        self.assertEqual(song.language, 'English')
        self.assertEqual(song.year, 2026)
        self.assertTrue(song.song_img.name.endswith('.jpg'))
        self.assertTrue(song.song_file.name.endswith('.mp3'))
        self.assertIn('CREATED: Authorised Test Song - Authorised Artist', output)

    def test_import_song_catalog_saves_cover_and_audio_using_field_storages(self):
        class RecordingStorage(Storage):
            def __init__(self):
                self.saved = []

            def _save(self, name, content):
                self.saved.append(name)
                return name

            def exists(self, name):
                return False

            def url(self, name):
                return '/recorded/{0}'.format(name)

        image_storage = RecordingStorage()
        audio_storage = RecordingStorage()
        image_field = Song._meta.get_field('song_img')
        audio_field = Song._meta.get_field('song_file')
        original_image_storage = image_field.storage
        original_audio_storage = audio_field.storage
        source_dir, manifest_path = self._catalog_source()
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        try:
            image_field.storage = image_storage
            audio_field.storage = audio_storage
            self._run_import('--source', str(source_dir), '--manifest', str(manifest_path), '--confirm-rights')
        finally:
            image_field.storage = original_image_storage
            audio_field.storage = original_audio_storage

        self.assertEqual(image_storage.saved, ['cover.jpg'])
        self.assertEqual(audio_storage.saved, ['song.mp3'])

    def test_import_song_catalog_second_run_is_idempotent(self):
        source_dir, manifest_path = self._catalog_source()
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        self._run_import('--source', str(source_dir), '--manifest', str(manifest_path), '--confirm-rights')
        before_ids = list(Song.objects.values_list('id', flat=True))
        output, _ = self._run_import('--source', str(source_dir), '--manifest', str(manifest_path), '--confirm-rights')

        self.assertEqual(Song.objects.count(), 1)
        self.assertEqual(list(Song.objects.values_list('id', flat=True)), before_ids)
        self.assertIn('Import summary: 0 created, 0 updated, 1 skipped, 0 failed.', output)

    def test_import_song_catalog_updates_existing_song_without_duplicate(self):
        source_dir, manifest_path = self._catalog_source(rows=[
            {
                'name': 'Authorised Test Song',
                'album': 'Updated Album',
                'language': 'Hindi',
                'year': 2027,
                'singer': 'Authorised Artist',
                'audio_filename': 'song.mp3',
                'cover_filename': 'cover.jpg',
            },
        ])
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)
        Song.objects.create(
            name='Authorised Test Song',
            album='Old Album',
            language='English',
            year=2020,
            singer='Authorised Artist',
        )

        output, _ = self._run_import('--source', str(source_dir), '--manifest', str(manifest_path), '--confirm-rights')

        song = Song.objects.get(name='Authorised Test Song', singer='Authorised Artist')
        self.assertEqual(Song.objects.count(), 1)
        self.assertEqual(song.album, 'Updated Album')
        self.assertEqual(song.language, 'Hindi')
        self.assertEqual(song.year, 2027)
        self.assertIn('UPDATED: Authorised Test Song - Authorised Artist', output)

    def test_import_song_catalog_reports_conflicting_records(self):
        source_dir, manifest_path = self._catalog_source()
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)
        Song.objects.create(
            name='Authorised Test Song',
            album='Other Album',
            language='English',
            year=2026,
            singer='Different Artist',
        )

        with self.assertRaisesMessage(CommandError, 'Conflicting record'):
            call_command('import_song_catalog', '--source', str(source_dir), '--manifest', str(manifest_path), '--dry-run')

    def test_import_song_catalog_reports_duplicate_manifest_song_names(self):
        source_dir, manifest_path = self._catalog_source(rows=[
            {
                'name': 'Duplicate Song',
                'album': 'Album One',
                'language': 'English',
                'year': 2026,
                'singer': 'Artist One',
                'audio_filename': 'song.mp3',
                'cover_filename': 'cover.jpg',
            },
            {
                'name': 'Duplicate Song',
                'album': 'Album Two',
                'language': 'Hindi',
                'year': 2026,
                'singer': 'Artist Two',
                'audio_filename': 'song.mp3',
                'cover_filename': 'cover.jpg',
            },
        ])
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        with self.assertRaisesMessage(CommandError, 'duplicate song name'):
            call_command('import_song_catalog', '--source', str(source_dir), '--manifest', str(manifest_path), '--dry-run')

    def test_import_song_catalog_demo_removal_requires_confirmation(self):
        call_command('seed_demo_catalog', stdout=StringIO())

        with self.assertRaisesMessage(CommandError, '--confirm-demo-removal is required'):
            call_command('import_song_catalog', '--remove-demo-catalog')

    def test_import_song_catalog_removes_only_exact_seeded_demo_records(self):
        call_command('seed_demo_catalog', stdout=StringIO())
        unrelated_song = Song.objects.create(
            name='Neon Courtyard',
            album='Custom Album',
            language='English',
            year=2026,
            singer='Aria Vale',
        )

        output, _ = self._run_import('--remove-demo-catalog', '--confirm-demo-removal')

        self.assertFalse(Song.objects.filter(album='Midnight Metro', name='Neon Courtyard').exists())
        self.assertTrue(Song.objects.filter(id=unrelated_song.id).exists())
        self.assertEqual(Song.objects.count(), 1)
        self.assertIn('Demo removal summary: 8 removed, 0 skipped with relationships.', output)

    def test_import_song_catalog_demo_removal_skips_related_records(self):
        user = User.objects.create_user(username='demo-listener', password='secret-pass')
        call_command('seed_demo_catalog', stdout=StringIO())
        related_song = Song.objects.get(name='Neon Courtyard', singer='Aria Vale')
        Favourite.objects.create(user=user, song=related_song, is_fav=True)

        output, _ = self._run_import('--remove-demo-catalog', '--confirm-demo-removal')

        self.assertTrue(Song.objects.filter(id=related_song.id).exists())
        self.assertEqual(Song.objects.count(), 1)
        self.assertIn('7 removed, 1 skipped with relationships', output)

    def test_import_song_catalog_failure_summary_reports_storage_error(self):
        class FailingStorage(Storage):
            def _save(self, name, content):
                raise OSError('storage unavailable')

            def exists(self, name):
                return False

        image_field = Song._meta.get_field('song_img')
        audio_field = Song._meta.get_field('song_file')
        original_image_storage = image_field.storage
        original_audio_storage = audio_field.storage
        source_dir, manifest_path = self._catalog_source()
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)

        try:
            image_field.storage = FailingStorage()
            audio_field.storage = FailingStorage()
            output, error = self._run_import(
                '--source',
                str(source_dir),
                '--manifest',
                str(manifest_path),
                '--confirm-rights',
            )
        finally:
            image_field.storage = original_image_storage
            audio_field.storage = original_audio_storage

        self.assertEqual(Song.objects.count(), 0)
        self.assertIn('Import summary: 0 created, 0 updated, 0 skipped, 1 failed.', output)
        self.assertIn('FAILED: Authorised Test Song - Authorised Artist', error)

    def test_import_song_catalog_tests_use_filesystem_storage_without_cloudinary(self):
        self.assertNotIn('cloudinary_storage', settings.INSTALLED_APPS)
        self.assertEqual(
            settings.STORAGES['default']['BACKEND'],
            'django.core.files.storage.FileSystemStorage',
        )
        self.assertNotEqual(type(Song._meta.get_field('song_img').storage).__name__, 'SonicaCloudinaryImageStorage')
        self.assertNotEqual(type(Song._meta.get_field('song_file').storage).__name__, 'SonicaCloudinaryAudioStorage')

    def test_song_upload_validation_does_not_use_real_project_media_root_in_tests(self):
        self.assertEqual(settings.MEDIA_ROOT, TEST_MEDIA_ROOT)
        self.assertNotEqual(settings.MEDIA_ROOT, settings.PROJECT_MEDIA_ROOT)

    def test_song_upload_validation_default_size_limits_are_documented_values(self):
        self.assertEqual(DEFAULT_MAX_AUDIO_UPLOAD_SIZE, 20 * 1024 * 1024)
        self.assertEqual(DEFAULT_MAX_COVER_UPLOAD_SIZE, 5 * 1024 * 1024)

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
            album='Test Album',
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

    def test_anonymous_favourite_routes_require_login(self):
        song = self._create_song()
        before = self._counts()

        get_response = self.client.get(reverse('favourite'))
        add_response = self.client.post(reverse('add_favourite', args=[song.id]))
        remove_response = self.client.post(reverse('remove_favourite', args=[song.id]))

        self.assertEqual(get_response.status_code, 302)
        self.assertEqual(add_response.status_code, 302)
        self.assertEqual(remove_response.status_code, 302)
        self.assertIn(reverse('login'), get_response['Location'])
        self.assertIn(reverse('login'), add_response['Location'])
        self.assertIn(reverse('login'), remove_response['Location'])
        self.assertEqual(self._counts(), before)

    def test_detail_get_does_not_create_favourite(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Favourite.objects.count(), 0)

    def test_detail_get_does_not_remove_favourite(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        Favourite.objects.create(user=user, song=song, is_fav=True)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._counts(), before)
        self.assertTrue(Favourite.objects.filter(user=user, song=song, is_fav=True).exists())

    def test_favourite_page_get_does_not_mutate_favourites(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        Favourite.objects.create(user=user, song=song, is_fav=True)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('favourite'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._counts(), before)

    def test_catalog_gets_do_not_mutate_favourites(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        Favourite.objects.create(user=user, song=song, is_fav=True)
        self.client.force_login(user)

        for url in [reverse('index'), reverse('all_songs')]:
            with self.subTest(url=url):
                before = self._counts()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self._counts(), before)

    def test_favourite_mutation_routes_are_post_only_for_authenticated_user(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        for url in [reverse('add_favourite', args=[song.id]), reverse('remove_favourite', args=[song.id])]:
            with self.subTest(url=url):
                before = self._counts()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(self._counts(), before)

    def test_add_favourite_is_idempotent(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        first_response = self.client.post(reverse('add_favourite', args=[song.id]))
        second_response = self.client.post(reverse('add_favourite', args=[song.id]))

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(Favourite.objects.filter(user=user, song=song, is_fav=True).count(), 1)
        self.assertEqual(Favourite.objects.filter(user=user, song=song).count(), 1)

    def test_add_favourite_reactivates_false_row_and_cleans_duplicate_current_user_rows(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        song = self._create_song()
        Favourite.objects.create(user=user, song=song, is_fav=False)
        Favourite.objects.create(user=user, song=song, is_fav=False)
        other_favourite = Favourite.objects.create(user=other_user, song=song, is_fav=True)
        self.client.force_login(user)

        response = self.client.post(reverse('add_favourite', args=[song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favourite.objects.filter(user=user, song=song, is_fav=True).count(), 1)
        self.assertEqual(Favourite.objects.filter(user=user, song=song).count(), 1)
        self.assertTrue(Favourite.objects.filter(id=other_favourite.id, is_fav=True).exists())

    def test_add_favourite_invalid_song_id_returns_404_without_mutation(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        Favourite.objects.create(user=user, song=song, is_fav=True)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.post(reverse('add_favourite', args=[999]))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._counts(), before)
        self.assertTrue(Song.objects.filter(id=song.id).exists())

    def test_add_favourite_uses_safe_redirect_or_detail_fallback(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        safe_response = self.client.post(reverse('add_favourite', args=[song.id]), {'next': reverse('all_songs')})
        blank_response = self.client.post(reverse('add_favourite', args=[song.id]), {'next': ''})
        missing_response = self.client.post(reverse('add_favourite', args=[song.id]))
        external_response = self.client.post(
            reverse('add_favourite', args=[song.id]),
            {'next': 'https://example.com/steal'},
        )
        protocol_relative_response = self.client.post(
            reverse('add_favourite', args=[song.id]),
            {'next': '//example.com/steal'},
        )

        self.assertEqual(safe_response['Location'], reverse('all_songs'))
        self.assertEqual(blank_response['Location'], reverse('detail', args=[song.id]))
        self.assertEqual(missing_response['Location'], reverse('detail', args=[song.id]))
        self.assertEqual(external_response['Location'], reverse('detail', args=[song.id]))
        self.assertEqual(protocol_relative_response['Location'], reverse('detail', args=[song.id]))

    def test_remove_favourite_is_scoped_to_current_user_and_preserves_song(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        song = self._create_song()
        Favourite.objects.create(user=owner, song=song, is_fav=True)
        Favourite.objects.create(user=other_user, song=song, is_fav=True)
        self.client.force_login(owner)

        response = self.client.post(reverse('remove_favourite', args=[song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Favourite.objects.filter(user=owner, song=song, is_fav=True).exists())
        self.assertTrue(Favourite.objects.filter(user=other_user, song=song, is_fav=True).exists())
        self.assertTrue(Song.objects.filter(id=song.id).exists())

    def test_remove_missing_favourite_does_not_crash(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        response = self.client.post(reverse('remove_favourite', args=[song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Favourite.objects.filter(user=user, song=song).exists())

    def test_remove_favourite_invalid_song_id_returns_404_without_mutation(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        Favourite.objects.create(user=user, song=song, is_fav=True)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.post(reverse('remove_favourite', args=[999]))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._counts(), before)
        self.assertTrue(Song.objects.filter(id=song.id).exists())

    def test_remove_favourite_uses_safe_redirect_or_favourite_fallback(self):
        user = User.objects.create_user(username='listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        safe_response = self.client.post(reverse('remove_favourite', args=[song.id]), {'next': reverse('all_songs')})
        blank_response = self.client.post(reverse('remove_favourite', args=[song.id]), {'next': ''})
        missing_response = self.client.post(reverse('remove_favourite', args=[song.id]))
        external_response = self.client.post(
            reverse('remove_favourite', args=[song.id]),
            {'next': 'https://example.com/steal'},
        )

        self.assertEqual(safe_response['Location'], reverse('all_songs'))
        self.assertEqual(blank_response['Location'], reverse('favourite'))
        self.assertEqual(missing_response['Location'], reverse('favourite'))
        self.assertEqual(external_response['Location'], reverse('favourite'))

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

    def test_anonymous_playlist_pages_require_login(self):
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(
            user=User.objects.create_user(username='playlist-owner', password='secret-pass'),
            name='Road Trip',
        )
        before = self._counts()

        responses = [
            self.client.get(reverse('playlist')),
            self.client.get(reverse('playlist_songs', args=[playlist.id])),
            self.client.post(reverse('create_playlist'), {'playlist_name': 'New Mix'}),
            self.client.post(reverse('rename_playlist', args=[playlist.id]), {'playlist_name': 'Renamed'}),
            self.client.post(reverse('delete_playlist', args=[playlist.id])),
            self.client.post(reverse('add_song_to_playlist', args=[playlist.id, song.id])),
            self.client.post(reverse('remove_song_from_playlist', args=[playlist.id, song.id])),
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
        self.assertEqual(PlaylistContainer.objects.count(), 0)
        self.assertEqual(PlaylistSong.objects.count(), 0)

    def test_create_playlist_creates_empty_normalized_playlist(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        self.client.force_login(user)
        before_legacy = Playlist.objects.count()

        response = self.client.post(reverse('create_playlist'), {'playlist_name': '  Road Trip  '})

        self.assertEqual(response.status_code, 302)
        playlist = PlaylistContainer.objects.get(user=user, name='Road Trip')
        self.assertEqual(PlaylistSong.objects.filter(playlist=playlist).count(), 0)
        self.assertEqual(Playlist.objects.count(), before_legacy)

    def test_create_playlist_rejects_blank_duplicate_and_overlong_names(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        self.client.force_login(user)
        max_length = PlaylistContainer._meta.get_field('name').max_length

        for payload in [
            {'playlist_name': ''},
            {'playlist_name': '   '},
            {'playlist_name': 'Road Trip'},
            {'playlist_name': 'x' * (max_length + 1)},
        ]:
            with self.subTest(payload=payload):
                before = self._counts()
                response = self.client.post(reverse('create_playlist'), payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self._counts(), before)

    def test_create_playlist_allows_same_name_for_different_users(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        PlaylistContainer.objects.create(user=other_user, name='Road Trip')
        self.client.force_login(owner)

        response = self.client.post(reverse('create_playlist'), {'playlist_name': 'Road Trip'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PlaylistContainer.objects.filter(name='Road Trip').count(), 2)

    def test_playlist_list_empty_state_renders_without_mutation(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('playlist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'There are no playlists yet.')
        self.assertEqual(self._counts(), before)

    def test_detail_playlist_action_no_longer_mutates_playlists(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        response = self.client.post(
            reverse('detail', args=[song.id]),
            {'playlist_action': 'create', 'playlist_name': 'Road Trip'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Playlist.objects.exists())
        self.assertFalse(PlaylistContainer.objects.exists())
        self.assertFalse(PlaylistSong.objects.exists())

    def test_detail_page_lists_normalized_containers_for_add_actions(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        PlaylistContainer.objects.create(user=other_user, name='Other Mix')
        self.client.force_login(user)

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Road Trip')
        self.assertContains(response, reverse('add_song_to_playlist', args=[playlist.id, song.id]))
        self.assertNotContains(response, 'Other Mix')

    def test_add_song_to_playlist_is_normalized_and_idempotent(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        self.client.force_login(user)

        first_response = self.client.post(reverse('add_song_to_playlist', args=[playlist.id, song.id]))
        second_response = self.client.post(reverse('add_song_to_playlist', args=[playlist.id, song.id]))

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(PlaylistSong.objects.filter(playlist=playlist, song=song).count(), 1)
        self.assertEqual(Playlist.objects.count(), 0)

    def test_same_song_can_be_added_to_different_owned_playlists(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        first_playlist = PlaylistContainer.objects.create(user=user, name='Morning')
        second_playlist = PlaylistContainer.objects.create(user=user, name='Evening')
        self.client.force_login(user)

        first_response = self.client.post(reverse('add_song_to_playlist', args=[first_playlist.id, song.id]))
        second_response = self.client.post(reverse('add_song_to_playlist', args=[second_playlist.id, song.id]))

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(PlaylistSong.objects.filter(song=song).count(), 2)

    def test_add_song_rejects_invalid_or_foreign_playlist_and_song(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        playlist = PlaylistContainer.objects.create(user=other_user, name='Other Mix')
        song = self._create_song()
        self.client.force_login(owner)

        responses = [
            self.client.post(reverse('add_song_to_playlist', args=[playlist.id, song.id])),
            self.client.post(reverse('add_song_to_playlist', args=[999, song.id])),
            self.client.post(reverse('add_song_to_playlist', args=[playlist.id, 999])),
        ]

        for response in responses:
            with self.subTest(status=response.status_code):
                self.assertEqual(response.status_code, 404)
        self.assertFalse(PlaylistSong.objects.exists())

    def test_playlist_page_lists_current_user_playlists_and_song_counts(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        first_song = self._create_song(name='First Playlist Song')
        second_song = self._create_song(name='Second Playlist Song')
        playlist = PlaylistContainer.objects.create(user=owner, name='Road Trip')
        PlaylistSong.objects.create(playlist=playlist, song=first_song)
        PlaylistSong.objects.create(playlist=playlist, song=second_song)
        PlaylistContainer.objects.create(user=owner, name='Empty Mix')
        PlaylistContainer.objects.create(user=other_user, name='Other Mix')
        self.client.force_login(owner)

        response = self.client.get(reverse('playlist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Road Trip')
        self.assertContains(response, '2 songs')
        self.assertContains(response, 'Empty Mix')
        self.assertContains(response, '0 songs')
        self.assertNotContains(response, 'Other Mix')

    def test_runtime_pages_ignore_legacy_only_playlist_rows(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        Playlist.objects.create(user=user, song=song, playlist_name='Legacy Only')
        self.client.force_login(user)

        playlist_response = self.client.get(reverse('playlist'))
        detail_response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(playlist_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertNotContains(playlist_response, 'Legacy Only')
        self.assertNotContains(detail_response, 'Legacy Only')
        self.assertEqual(Playlist.objects.count(), 1)

    def test_playlist_detail_renders_empty_playlist_without_mutation(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        playlist = PlaylistContainer.objects.create(user=user, name='Empty Mix')
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('playlist_songs', args=[playlist.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This playlist is empty.')
        self.assertEqual(self._counts(), before)

    def test_playlist_detail_orders_songs_by_membership_order(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        playlist = PlaylistContainer.objects.create(user=user, name='Ordered Mix')
        first_song = self._create_song(name='Alpha Runtime Song')
        second_song = self._create_song(name='Beta Runtime Song')
        PlaylistSong.objects.create(playlist=playlist, song=first_song)
        PlaylistSong.objects.create(playlist=playlist, song=second_song)
        self.client.force_login(user)

        response = self.client.get(reverse('playlist_songs', args=[playlist.id]))
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertLess(content.index('Alpha Runtime Song'), content.index('Beta Runtime Song'))

    def test_playlist_songs_page_is_id_based_and_user_scoped(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        owner_song = self._create_song(name='Owner Playlist Song')
        other_song = self._create_song(name='Other Playlist Song')
        playlist = PlaylistContainer.objects.create(user=owner, name='Shared Name')
        other_playlist = PlaylistContainer.objects.create(user=other_user, name='Other Name')
        PlaylistSong.objects.create(playlist=playlist, song=owner_song)
        PlaylistSong.objects.create(playlist=other_playlist, song=other_song)
        self.client.force_login(owner)

        own_response = self.client.get(reverse('playlist_songs', args=[playlist.id]))
        other_response = self.client.get(reverse('playlist_songs', args=[other_playlist.id]))

        self.assertEqual(own_response.status_code, 200)
        self.assertContains(own_response, 'Owner Playlist Song')
        self.assertNotContains(own_response, 'Other Playlist Song')
        self.assertEqual(other_response.status_code, 404)

    def test_playlist_songs_missing_media_renders_fallbacks(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = Song.objects.create(
            name='Blank Playlist Song',
            album='Test Album',
            language='English',
            year=2026,
            singer='Test Singer',
        )
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        PlaylistSong.objects.create(playlist=playlist, song=song)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('playlist_songs', args=[playlist.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cover unavailable')
        self.assertContains(response, 'Audio unavailable.')
        self.assertEqual(self._counts(), before)

    def test_playlist_remove_requires_valid_song_id(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        PlaylistSong.objects.create(playlist=playlist, song=song)
        self.client.force_login(user)

        before = self._counts()
        response = self.client.post(reverse('remove_song_from_playlist', args=[playlist.id, 999]))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._counts(), before)

    def test_playlist_remove_is_scoped_and_preserves_empty_container(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(user=owner, name='Shared Name')
        other_playlist = PlaylistContainer.objects.create(user=other_user, name='Shared Name')
        PlaylistSong.objects.create(playlist=playlist, song=song)
        PlaylistSong.objects.create(playlist=other_playlist, song=song)
        self.client.force_login(owner)

        response = self.client.post(reverse('remove_song_from_playlist', args=[playlist.id, song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(PlaylistContainer.objects.filter(id=playlist.id).exists())
        self.assertFalse(PlaylistSong.objects.filter(playlist=playlist, song=song).exists())
        self.assertTrue(PlaylistSong.objects.filter(playlist=other_playlist, song=song).exists())
        empty_response = self.client.get(reverse('playlist_songs', args=[playlist.id]))
        self.assertEqual(empty_response.status_code, 200)
        self.assertContains(empty_response, 'This playlist is empty.')

        foreign_remove = self.client.post(reverse('remove_song_from_playlist', args=[other_playlist.id, song.id]))
        self.assertEqual(foreign_remove.status_code, 404)
        self.assertTrue(PlaylistSong.objects.filter(playlist=other_playlist, song=song).exists())

    def test_removing_missing_membership_does_not_crash(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        self.client.force_login(user)

        response = self.client.post(reverse('remove_song_from_playlist', args=[playlist.id, song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(PlaylistContainer.objects.filter(id=playlist.id).exists())

    def test_remove_song_does_not_delete_song_record(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        PlaylistSong.objects.create(playlist=playlist, song=song)
        self.client.force_login(user)

        response = self.client.post(reverse('remove_song_from_playlist', args=[playlist.id, song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Song.objects.filter(id=song.id).exists())

    def test_rename_playlist_trims_and_rejects_duplicate_or_foreign_playlist(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        playlist = PlaylistContainer.objects.create(user=owner, name='Road Trip')
        PlaylistContainer.objects.create(user=owner, name='Focus')
        other_playlist = PlaylistContainer.objects.create(user=other_user, name='Other Mix')
        self.client.force_login(owner)

        response = self.client.post(reverse('rename_playlist', args=[playlist.id]), {'playlist_name': '  New Road  '})
        self.assertEqual(response.status_code, 302)
        playlist.refresh_from_db()
        self.assertEqual(playlist.name, 'New Road')

        duplicate = self.client.post(reverse('rename_playlist', args=[playlist.id]), {'playlist_name': 'Focus'})
        blank = self.client.post(reverse('rename_playlist', args=[playlist.id]), {'playlist_name': '   '})
        foreign = self.client.post(reverse('rename_playlist', args=[other_playlist.id]), {'playlist_name': 'Hidden'})
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(blank.status_code, 400)
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(PlaylistContainer.objects.get(id=other_playlist.id).name, 'Other Mix')

    def test_rename_allows_same_name_owned_by_different_user(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        playlist = PlaylistContainer.objects.create(user=owner, name='Road Trip')
        PlaylistContainer.objects.create(user=other_user, name='Focus')
        self.client.force_login(owner)

        response = self.client.post(reverse('rename_playlist', args=[playlist.id]), {'playlist_name': 'Focus'})

        self.assertEqual(response.status_code, 302)
        playlist.refresh_from_db()
        self.assertEqual(playlist.name, 'Focus')

    def test_delete_playlist_removes_memberships_not_songs_or_legacy_rows(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        PlaylistSong.objects.create(playlist=playlist, song=song)
        Playlist.objects.create(user=user, playlist_name='Legacy Mix', song=song)
        self.client.force_login(user)

        response = self.client.post(reverse('delete_playlist', args=[playlist.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(PlaylistContainer.objects.filter(id=playlist.id).exists())
        self.assertFalse(PlaylistSong.objects.filter(playlist_id=playlist.id).exists())
        self.assertTrue(Song.objects.filter(id=song.id).exists())
        self.assertTrue(Playlist.objects.filter(user=user, playlist_name='Legacy Mix', song=song).exists())

    def test_delete_playlist_is_scoped_to_current_user(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        playlist = PlaylistContainer.objects.create(user=other_user, name='Other Mix')
        self.client.force_login(owner)

        response = self.client.post(reverse('delete_playlist', args=[playlist.id]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(PlaylistContainer.objects.filter(id=playlist.id).exists())

    def test_legacy_rows_remain_unchanged_across_normalized_operations(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        legacy = Playlist.objects.create(user=user, playlist_name='Legacy Mix', song=song)
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        self.client.force_login(user)

        self.client.post(reverse('add_song_to_playlist', args=[playlist.id, song.id]))
        self.client.post(reverse('rename_playlist', args=[playlist.id]), {'playlist_name': 'New Road'})
        self.client.post(reverse('remove_song_from_playlist', args=[playlist.id, song.id]))
        self.client.post(reverse('delete_playlist', args=[playlist.id]))

        legacy.refresh_from_db()
        self.assertEqual(legacy.playlist_name, 'Legacy Mix')
        self.assertEqual(legacy.song_id, song.id)
        self.assertEqual(Playlist.objects.count(), 1)

    def test_playlist_mutations_are_post_only(self):
        user = User.objects.create_user(username='playlist-listener', password='secret-pass')
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(user=user, name='Road Trip')
        self.client.force_login(user)

        urls = [
            reverse('create_playlist'),
            reverse('rename_playlist', args=[playlist.id]),
            reverse('delete_playlist', args=[playlist.id]),
            reverse('add_song_to_playlist', args=[playlist.id, song.id]),
            reverse('remove_song_from_playlist', args=[playlist.id, song.id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                before = self._counts()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(self._counts(), before)

    def test_anonymous_playback_routes_require_login(self):
        song = self._create_song()
        before = self._counts()

        routes = [
            reverse('play_song', args=[song.id]),
            reverse('play_song_index', args=[song.id]),
            reverse('play_recent_song', args=[song.id]),
            reverse('record_song_play', args=[song.id]),
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

    def test_playback_get_routes_do_not_record_recent_for_current_user(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        for url in [
            reverse('play_song', args=[song.id]),
            reverse('play_song_index', args=[song.id]),
            reverse('play_recent_song', args=[song.id]),
        ]:
            with self.subTest(url=url):
                before = self._counts()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(self._counts(), before)

    def test_playback_get_routes_do_not_reorder_recent_history(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        first_song = self._create_song(name='First Recent Song')
        second_song = self._create_song(name='Second Recent Song')
        Recent.objects.create(user=user, song=first_song)
        Recent.objects.create(user=user, song=second_song)
        self.client.force_login(user)
        before_order = list(Recent.objects.values_list('id', 'song_id').order_by('-id'))

        response = self.client.get(reverse('play_song', args=[first_song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(Recent.objects.values_list('id', 'song_id').order_by('-id')), before_order)

    def test_record_song_play_post_records_recent_for_current_user(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        response = self.client.post(reverse('record_song_play', args=[song.id]), {'next': reverse('all_songs')})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('all_songs'))
        self.assertEqual(Recent.objects.filter(user=user, song=song).count(), 1)

    def test_repeated_record_song_play_moves_song_to_newest_without_duplicates(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        first_song = self._create_song(name='First Recent Song')
        second_song = self._create_song(name='Second Recent Song')
        self.client.force_login(user)

        self.client.post(reverse('record_song_play', args=[first_song.id]))
        self.client.post(reverse('record_song_play', args=[second_song.id]))
        self.client.post(reverse('record_song_play', args=[first_song.id]))

        rows = list(Recent.objects.filter(user=user).order_by('-id'))
        self.assertEqual([row.song for row in rows], [first_song, second_song])
        self.assertEqual(Recent.objects.filter(user=user, song=first_song).count(), 1)

    def test_record_song_play_cleans_historical_duplicate_rows(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        song = self._create_song()
        Recent.objects.create(user=user, song=song)
        Recent.objects.create(user=user, song=song)
        self.client.force_login(user)

        response = self.client.post(reverse('record_song_play', args=[song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Recent.objects.filter(user=user, song=song).count(), 1)

    def test_record_song_play_history_is_scoped_to_current_user(self):
        owner = User.objects.create_user(username='owner', password='secret-pass')
        other_user = User.objects.create_user(username='other-listener', password='secret-pass')
        song = self._create_song()
        Recent.objects.create(user=other_user, song=song)
        self.client.force_login(owner)

        response = self.client.post(reverse('record_song_play', args=[song.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Recent.objects.filter(user=owner, song=song).count(), 1)
        self.assertEqual(Recent.objects.filter(user=other_user, song=song).count(), 1)

    def test_record_song_play_invalid_song_id_returns_404_without_history_mutation(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        self.client.force_login(user)
        before = self._counts()

        response = self.client.post(reverse('record_song_play', args=[999]))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._counts(), before)

    def test_record_song_play_get_is_post_only(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('record_song_play', args=[song.id]))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(self._counts(), before)

    def test_record_song_play_uses_safe_redirect_or_detail_fallback(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        safe_response = self.client.post(reverse('record_song_play', args=[song.id]), {'next': reverse('recent')})
        external_response = self.client.post(
            reverse('record_song_play', args=[song.id]),
            {'next': 'https://example.com/steal'},
        )
        blank_response = self.client.post(reverse('record_song_play', args=[song.id]), {'next': ''})
        missing_response = self.client.post(reverse('record_song_play', args=[song.id]))

        self.assertEqual(safe_response['Location'], reverse('recent'))
        self.assertEqual(external_response['Location'], reverse('detail', args=[song.id]))
        self.assertEqual(blank_response['Location'], reverse('detail', args=[song.id]))
        self.assertEqual(missing_response['Location'], reverse('detail', args=[song.id]))

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
        first_play_url = reverse('record_song_play', args=[first_song.id])
        second_play_url = reverse('record_song_play', args=[second_song.id])

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, first_play_url, count=1)
        self.assertContains(response, second_play_url, count=1)
        self.assertLess(content.index(first_play_url), content.index(second_play_url))

    def test_song_card_play_controls_are_post_forms_with_csrf(self):
        user = User.objects.create_user(username='playback-listener', password='secret-pass')
        song = self._create_song()
        self.client.force_login(user)

        response = self.client.get(reverse('all_songs'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'method="post"')
        self.assertContains(response, reverse('record_song_play', args=[song.id]))
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertNotContains(response, 'href="{0}"'.format(reverse('play_song', args=[song.id])))

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
            album='Test Album',
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

    def test_detail_favourite_add_form_posts_with_csrf_and_no_mutation_anchor(self):
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        song = self._create_song_with_media_state('Detail Favourite Form Song')
        self.client.force_login(user)
        add_url = reverse('add_favourite', args=[song.id])

        response = self.client.get(reverse('detail', args=[song.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'method="post" action="{}"'.format(add_url))
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'Add to Favourites')
        self.assertNotContains(response, 'href="{}"'.format(add_url))

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

    def test_favourite_page_remove_form_posts_with_csrf_and_no_mutation_anchor(self):
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        song = self._create_song_with_media_state('Favourite Remove Form Song')
        Favourite.objects.create(user=user, song=song, is_fav=True)
        self.client.force_login(user)
        remove_url = reverse('remove_favourite', args=[song.id])

        response = self.client.get(reverse('favourite'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'method="post"')
        self.assertContains(response, 'action="{}"'.format(remove_url))
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'Remove')
        self.assertNotContains(response, 'href="{}"'.format(remove_url))

    def test_blank_media_song_renders_safely_on_playlist_songs_page(self):
        user = User.objects.create_user(username='media-listener', password='secret-pass')
        song = self._create_song_with_media_state('Blank Playlist Media Song')
        playlist = PlaylistContainer.objects.create(user=user, name='Media Mix')
        PlaylistSong.objects.create(playlist=playlist, song=song)
        self.client.force_login(user)
        before = self._counts()

        response = self.client.get(reverse('playlist_songs', args=[playlist.id]))

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
            reverse('playlist_songs', args=[999]),
        ]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response['Location'])

    def test_project_smoke_harness_command_passes_and_reports_totals(self):
        with transaction.atomic():
            results = run_smoke_checks()
            report = render_report(results)
            transaction.set_rollback(True)

        self.assertIn('PASS', report)
        self.assertIn('Total checks:', report)
        self.assertIn('Failed checks: 0', report)
        self.assertIn('Overall result: PASS', report)
        self.assertIn('POST record-play route', report)
        self.assertTrue(all(result['passed'] for result in results))

    def test_project_smoke_harness_detects_wrong_expectation(self):
        with transaction.atomic():
            results = run_smoke_checks(expect_overrides={'public:index': 404})
            transaction.set_rollback(True)

        report = render_report(results)
        self.assertIn('FAIL', report)
        self.assertTrue(any(not result['passed'] for result in results))

    def test_project_smoke_harness_leaves_row_counts_unchanged(self):
        before = self._counts()
        before['users'] = User.objects.count()

        with transaction.atomic():
            results = run_smoke_checks()
            transaction.set_rollback(True)

        after = self._counts()
        after['users'] = User.objects.count()
        self.assertTrue(all(result['passed'] for result in results))
        self.assertEqual(after, before)

    def test_project_smoke_command_and_compatibility_alias_pass(self):
        project_output = StringIO()
        alias_output = StringIO()

        call_command('project_smoke_test', stdout=project_output)
        call_command('recovery_smoke_test', stdout=alias_output)

        self.assertIn('Overall result: PASS', project_output.getvalue())
        self.assertIn('Overall result: PASS', alias_output.getvalue())

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

    def test_seed_demo_catalog_first_run_creates_exact_fictional_catalog(self):
        output = StringIO()

        call_command('seed_demo_catalog', stdout=output)

        self.assertEqual(Song.objects.count(), 8)
        self.assertEqual(len(DEMO_CATALOG_SONGS), 8)
        self.assertIn('8 created, 0 updated, 0 skipped', output.getvalue())
        self.assertIn('Final catalogue totals: 8 songs (4 Hindi, 4 English)', output.getvalue())

    def test_seed_demo_catalog_second_run_is_idempotent(self):
        first_output = StringIO()
        second_output = StringIO()

        call_command('seed_demo_catalog', stdout=first_output)
        before_ids = list(Song.objects.values_list('id', flat=True).order_by('id'))
        call_command('seed_demo_catalog', stdout=second_output)

        self.assertEqual(Song.objects.count(), 8)
        self.assertEqual(
            list(Song.objects.values_list('id', flat=True).order_by('id')),
            before_ids,
        )
        self.assertIn('0 created, 0 updated, 8 skipped', second_output.getvalue())

    def test_seed_demo_catalog_populates_four_hindi_and_four_english_songs(self):
        call_command('seed_demo_catalog', stdout=StringIO())

        self.assertEqual(Song.objects.filter(language='Hindi').count(), 4)
        self.assertEqual(Song.objects.filter(language='English').count(), 4)
        self.assertTrue(Song.objects.filter(name='Chand Ki Raah', singer='Aarav Mehta').exists())
        self.assertTrue(Song.objects.filter(name='Neon Courtyard', singer='Aria Vale').exists())

    def test_seed_demo_catalog_leaves_audio_and_cover_fields_blank(self):
        call_command('seed_demo_catalog', stdout=StringIO())

        for song in Song.objects.order_by('name'):
            self.assertEqual(song.song_img.name, '')
            self.assertEqual(song.song_file.name, '')

    def test_seed_demo_catalog_updates_existing_seeded_row_without_duplication(self):
        Song.objects.create(
            name='Neon Courtyard',
            album='Outdated Album',
            language='Hindi',
            year=2020,
            singer='Aria Vale',
        )
        output = StringIO()

        call_command('seed_demo_catalog', stdout=output)

        song = Song.objects.get(name='Neon Courtyard', singer='Aria Vale')
        self.assertEqual(song.album, 'Midnight Metro')
        self.assertEqual(song.language, 'English')
        self.assertEqual(song.year, 2026)
        self.assertEqual(Song.objects.count(), 8)
        self.assertIn('7 created, 1 updated, 0 skipped', output.getvalue())

    def test_seed_demo_catalog_leaves_unrelated_user_created_songs_untouched(self):
        unrelated_song = Song.objects.create(
            name='Personal Draft',
            album='Private Album',
            language='English',
            year=2023,
            singer='Local Artist',
            song_img=SimpleUploadedFile('personal-cover.jpg', b'cover-bytes', content_type='image/jpeg'),
            song_file=SimpleUploadedFile('personal-song.mp3', b'audio-bytes', content_type='audio/mpeg'),
        )

        call_command('seed_demo_catalog', stdout=StringIO())
        unrelated_song.refresh_from_db()

        self.assertEqual(Song.objects.count(), 9)
        self.assertEqual(unrelated_song.album, 'Private Album')
        self.assertEqual(unrelated_song.language, 'English')
        self.assertEqual(unrelated_song.year, 2023)
        self.assertEqual(unrelated_song.singer, 'Local Artist')
        self.assertEqual(unrelated_song.song_img.name, 'personal-cover.jpg')
        self.assertEqual(unrelated_song.song_file.name, 'personal-song.mp3')


class PlaylistSchemaFoundationTests(TestCase):
    def _create_song(self, name='Schema Test Song'):
        return Song.objects.create(
            name=name,
            album='Schema Album',
            language='English',
            year=2026,
            singer='Schema Singer',
        )

    def test_playlist_container_can_exist_without_songs(self):
        user = User.objects.create_user(username='schema-listener', password='secret-pass')

        playlist = PlaylistContainer.objects.create(user=user, name='Empty Future Mix')

        self.assertEqual(playlist.user, user)
        self.assertEqual(playlist.name, 'Empty Future Mix')
        self.assertEqual(playlist.songs.count(), 0)
        self.assertIsNotNone(playlist.created_at)
        self.assertIsNotNone(playlist.updated_at)

    def test_playlist_container_name_is_unique_per_user(self):
        owner = User.objects.create_user(username='schema-owner', password='secret-pass')
        other_user = User.objects.create_user(username='schema-other', password='secret-pass')
        PlaylistContainer.objects.create(user=owner, name='Focus')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaylistContainer.objects.create(user=owner, name='Focus')

        PlaylistContainer.objects.create(user=other_user, name='Focus')
        self.assertEqual(PlaylistContainer.objects.filter(name='Focus').count(), 2)

    def test_playlist_song_membership_is_unique_per_container(self):
        user = User.objects.create_user(username='schema-member', password='secret-pass')
        song = self._create_song()
        playlist = PlaylistContainer.objects.create(user=user, name='Focus')
        PlaylistSong.objects.create(playlist=playlist, song=song)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaylistSong.objects.create(playlist=playlist, song=song)

        self.assertEqual(PlaylistSong.objects.filter(playlist=playlist, song=song).count(), 1)

    def test_same_song_can_belong_to_different_playlist_containers(self):
        user = User.objects.create_user(username='schema-cross-member', password='secret-pass')
        song = self._create_song()
        first_playlist = PlaylistContainer.objects.create(user=user, name='Morning')
        second_playlist = PlaylistContainer.objects.create(user=user, name='Evening')

        PlaylistSong.objects.create(playlist=first_playlist, song=song)
        PlaylistSong.objects.create(playlist=second_playlist, song=song)

        self.assertEqual(PlaylistSong.objects.filter(song=song).count(), 2)

    def test_new_schema_does_not_backfill_or_change_legacy_playlist_rows(self):
        user = User.objects.create_user(username='legacy-schema-owner', password='secret-pass')
        song = self._create_song()
        Playlist.objects.create(user=user, song=song, playlist_name='Legacy Mix')

        self.assertEqual(Playlist.objects.count(), 1)
        self.assertEqual(PlaylistContainer.objects.count(), 0)
        self.assertEqual(PlaylistSong.objects.count(), 0)

    def test_legacy_playlist_behavior_still_allows_empty_name_duplicates(self):
        user = User.objects.create_user(username='legacy-duplicate-owner', password='secret-pass')
        song = self._create_song()

        Playlist.objects.create(user=user, song=song, playlist_name='Legacy Mix')
        Playlist.objects.create(user=user, song=song, playlist_name='Legacy Mix')

        self.assertEqual(
            Playlist.objects.filter(user=user, song=song, playlist_name='Legacy Mix').count(),
            2,
        )


class PlaylistDataMigrationTests(TransactionTestCase):
    migrate_from = [('musicapp', '0006_playlistcontainer_playlistsong_and_more')]
    migrate_to = [('musicapp', '0007_backfill_normalized_playlist_data')]

    def setUp(self):
        super().setUp()
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_from)
        self.old_apps = self.executor.loader.project_state(self.migrate_from).apps

    def tearDown(self):
        self.executor.migrate(self.migrate_to)
        super().tearDown()

    def _create_song(self, SongModel, name):
        return SongModel.objects.create(
            name=name,
            album='Migration Album',
            language='English',
            year=2026,
            singer='Migration Singer',
        )

    def _migrate_forward(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_to)
        return self.executor.loader.project_state(self.migrate_to).apps

    def _migrate_backward(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_from)
        return self.executor.loader.project_state(self.migrate_from).apps

    def test_forward_reverse_and_reapply_preserve_legacy_playlist_data(self):
        UserModel = self.old_apps.get_model('auth', 'User')
        SongModel = self.old_apps.get_model('musicapp', 'Song')
        LegacyPlaylist = self.old_apps.get_model('musicapp', 'Playlist')
        PlaylistContainerModel = self.old_apps.get_model('musicapp', 'PlaylistContainer')
        PlaylistSongModel = self.old_apps.get_model('musicapp', 'PlaylistSong')

        owner = UserModel.objects.create_user(username='migration-owner', password='secret-pass')
        other_user = UserModel.objects.create_user(username='migration-other', password='secret-pass')
        first_song = self._create_song(SongModel, 'Migration Song One')
        second_song = self._create_song(SongModel, 'Migration Song Two')
        unrelated_song = self._create_song(SongModel, 'Migration Song Three')

        preexisting_container = PlaylistContainerModel.objects.create(user=owner, name='Existing')
        preexisting_membership = PlaylistSongModel.objects.create(
            playlist=preexisting_container,
            song=first_song,
        )
        unrelated_container = PlaylistContainerModel.objects.create(user=owner, name='Unrelated Normalized')
        unrelated_membership = PlaylistSongModel.objects.create(
            playlist=unrelated_container,
            song=unrelated_song,
        )

        LegacyPlaylist.objects.create(user=owner, playlist_name='Focus', song=first_song)
        LegacyPlaylist.objects.create(user=owner, playlist_name='Focus', song=first_song)
        LegacyPlaylist.objects.create(user=owner, playlist_name='Focus', song=second_song)
        LegacyPlaylist.objects.create(user=owner, playlist_name='focus', song=first_song)
        LegacyPlaylist.objects.create(user=owner, playlist_name=' Focus', song=first_song)
        LegacyPlaylist.objects.create(user=owner, playlist_name='', song=first_song)
        LegacyPlaylist.objects.create(user=other_user, playlist_name='Focus', song=first_song)
        LegacyPlaylist.objects.create(user=owner, playlist_name='Existing', song=first_song)

        legacy_rows_before = list(
            LegacyPlaylist.objects
            .values_list('user_id', 'playlist_name', 'song_id')
            .order_by('id')
        )

        new_apps = self._migrate_forward()
        NewLegacyPlaylist = new_apps.get_model('musicapp', 'Playlist')
        NewPlaylistContainer = new_apps.get_model('musicapp', 'PlaylistContainer')
        NewPlaylistSong = new_apps.get_model('musicapp', 'PlaylistSong')

        self.assertEqual(
            list(NewLegacyPlaylist.objects.values_list('user_id', 'playlist_name', 'song_id').order_by('id')),
            legacy_rows_before,
        )
        self.assertEqual(NewPlaylistContainer.objects.filter(user_id=owner.id, name='Focus').count(), 1)
        self.assertEqual(NewPlaylistContainer.objects.filter(user_id=owner.id, name='focus').count(), 1)
        self.assertEqual(NewPlaylistContainer.objects.filter(user_id=owner.id, name=' Focus').count(), 1)
        self.assertEqual(NewPlaylistContainer.objects.filter(user_id=owner.id, name='').count(), 1)
        self.assertEqual(NewPlaylistContainer.objects.filter(user_id=other_user.id, name='Focus').count(), 1)
        self.assertEqual(NewPlaylistContainer.objects.count(), 7)

        owner_focus = NewPlaylistContainer.objects.get(user_id=owner.id, name='Focus')
        other_focus = NewPlaylistContainer.objects.get(user_id=other_user.id, name='Focus')
        existing = NewPlaylistContainer.objects.get(user_id=owner.id, name='Existing')
        self.assertEqual(NewPlaylistSong.objects.filter(playlist=owner_focus).count(), 2)
        self.assertEqual(NewPlaylistSong.objects.filter(playlist=other_focus).count(), 1)
        self.assertEqual(NewPlaylistSong.objects.filter(playlist=existing, song_id=first_song.id).count(), 1)
        self.assertEqual(NewPlaylistSong.objects.filter(playlist_id=preexisting_container.id).count(), 1)
        self.assertEqual(NewPlaylistSong.objects.filter(playlist_id=unrelated_container.id).count(), 1)
        self.assertEqual(NewPlaylistSong.objects.count(), 8)

        old_apps_after_reverse = self._migrate_backward()
        ReversedLegacyPlaylist = old_apps_after_reverse.get_model('musicapp', 'Playlist')
        ReversedPlaylistContainer = old_apps_after_reverse.get_model('musicapp', 'PlaylistContainer')
        ReversedPlaylistSong = old_apps_after_reverse.get_model('musicapp', 'PlaylistSong')

        self.assertEqual(
            list(ReversedLegacyPlaylist.objects.values_list('user_id', 'playlist_name', 'song_id').order_by('id')),
            legacy_rows_before,
        )
        self.assertTrue(ReversedPlaylistContainer.objects.filter(id=preexisting_container.id).exists())
        self.assertTrue(ReversedPlaylistContainer.objects.filter(id=unrelated_container.id).exists())
        self.assertTrue(ReversedPlaylistSong.objects.filter(id=preexisting_membership.id).exists())
        self.assertTrue(ReversedPlaylistSong.objects.filter(id=unrelated_membership.id).exists())
        self.assertEqual(ReversedPlaylistContainer.objects.count(), 2)
        self.assertEqual(ReversedPlaylistSong.objects.count(), 2)

        reapplied_apps = self._migrate_forward()
        ReappliedPlaylistContainer = reapplied_apps.get_model('musicapp', 'PlaylistContainer')
        ReappliedPlaylistSong = reapplied_apps.get_model('musicapp', 'PlaylistSong')
        self.assertEqual(ReappliedPlaylistContainer.objects.count(), 7)
        self.assertEqual(ReappliedPlaylistSong.objects.count(), 8)

    def test_forward_migration_handles_empty_legacy_table(self):
        new_apps = self._migrate_forward()
        NewLegacyPlaylist = new_apps.get_model('musicapp', 'Playlist')
        NewPlaylistContainer = new_apps.get_model('musicapp', 'PlaylistContainer')
        NewPlaylistSong = new_apps.get_model('musicapp', 'PlaylistSong')

        self.assertEqual(NewLegacyPlaylist.objects.count(), 0)
        self.assertEqual(NewPlaylistContainer.objects.count(), 0)
        self.assertEqual(NewPlaylistSong.objects.count(), 0)
