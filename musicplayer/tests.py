import os
import shutil
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, DEFAULT_DB_ALIAS, connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse


PRODUCTION_TEST_SECRET = 'production-settings-test-secret-value-with-enough-length-12345'
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class OperationalEndpointTests(TestCase):
    def test_health_endpoint_returns_200_with_minimal_json(self):
        response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_health_endpoint_does_not_query_database(self):
        with self.assertNumQueries(0):
            response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, 200)

    def test_ready_endpoint_returns_200_when_database_is_available(self):
        response = self.client.get(reverse('ready'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_ready_endpoint_uses_single_non_mutating_connectivity_query(self):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(reverse('ready'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(captured), 1)
        self.assertIn('SELECT 1', captured[0]['sql'])

    def test_ready_endpoint_returns_503_on_database_failure(self):
        with mock.patch('musicplayer.views.connection.cursor', side_effect=DatabaseError):
            response = self.client.get(reverse('ready'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})

    def test_ready_endpoint_does_not_expose_database_error_details(self):
        sensitive_error = DatabaseError('postgresql://sonica:secret-password@example.com:5432/sonica')

        with mock.patch('musicplayer.views.connection.cursor', side_effect=sensitive_error):
            response = self.client.get(reverse('ready'))

        content = response.content.decode()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret-password', content)
        self.assertNotIn('postgresql://', content)

    def test_operational_endpoints_do_not_expose_sensitive_details(self):
        for route_name in ['health', 'ready']:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                content = response.content.decode()

                self.assertNotIn(settings.SECRET_KEY, content)
                self.assertNotIn(str(settings.BASE_DIR), content)
                self.assertNotIn(str(settings.MEDIA_ROOT), content)
                self.assertNotIn(str(settings.STATIC_ROOT), content)

    def test_unsupported_methods_are_rejected_safely(self):
        for route_name in ['health', 'ready']:
            with self.subTest(route_name=route_name):
                response = self.client.post(reverse(route_name))

                self.assertEqual(response.status_code, 405)


class DeploymentReadinessTests(TestCase):
    def _settings_probe(self, extra_env, code):
        env = os.environ.copy()
        env.update(extra_env)
        python_paths = [str(PROJECT_ROOT)]
        if env.get('PYTHONPATH'):
            python_paths.append(env['PYTHONPATH'])
        env['PYTHONPATH'] = os.pathsep.join(python_paths)
        return subprocess.run(
            [sys.executable, '-c', code],
            cwd=str(PROJECT_ROOT),
            env=env,
            text=True,
            capture_output=True,
        )

    def test_wsgi_application_imports_successfully(self):
        from musicplayer.wsgi import application

        self.assertTrue(callable(application))

    def test_waitress_server_imports_successfully(self):
        import waitress

        self.assertTrue(hasattr(waitress, 'serve'))

    def test_sqlite_remains_default_without_database_url(self):
        result = self._settings_probe(
            {
                'DEBUG': 'True',
                'SECRET_KEY': 'settings-test-secret',
                'DATABASE_URL': '',
            },
            'import musicplayer.settings as settings; print(settings.DATABASES["default"]["ENGINE"])',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('django.db.backends.sqlite3', result.stdout)

    def test_postgresql_database_url_selects_postgresql_settings(self):
        result = self._settings_probe(
            {
                'DEBUG': 'False',
                'SECRET_KEY': PRODUCTION_TEST_SECRET,
                'ALLOWED_HOSTS': 'example.com',
                'DATABASE_URL': 'postgresql://sonica:secret-password@db.example.com:5432/sonica',
                'DATABASE_SSL_REQUIRE': 'True',
            },
            (
                'import musicplayer.settings as settings; '
                'db = settings.DATABASES["default"]; '
                'print(db["ENGINE"]); '
                'print(db["CONN_MAX_AGE"]); '
                'print(db["OPTIONS"].get("sslmode"))'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('django.db.backends.postgresql', result.stdout)
        self.assertIn('60', result.stdout)
        self.assertIn('require', result.stdout)
        self.assertNotIn('secret-password', result.stdout)

    def test_render_external_hostname_is_allowed_without_wildcard_hosts(self):
        result = self._settings_probe(
            {
                'DEBUG': 'False',
                'SECRET_KEY': PRODUCTION_TEST_SECRET,
                'ALLOWED_HOSTS': 'example.com',
                'RENDER_EXTERNAL_HOSTNAME': 'sonica-music-player.onrender.com',
            },
            (
                'import musicplayer.settings as settings; '
                'print(settings.ALLOWED_HOSTS); '
                'print(settings.CSRF_TRUSTED_ORIGINS)'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('sonica-music-player.onrender.com', result.stdout)
        self.assertIn('https://sonica-music-player.onrender.com', result.stdout)
        self.assertNotIn("'*'", result.stdout)

    def test_render_external_hostname_parses_url_style_value(self):
        result = self._settings_probe(
            {
                'DEBUG': 'False',
                'SECRET_KEY': PRODUCTION_TEST_SECRET,
                'ALLOWED_HOSTS': 'example.com',
                'RENDER_EXTERNAL_HOSTNAME': 'https://sonica-music-player.onrender.com',
            },
            (
                'import musicplayer.settings as settings; '
                'print(settings.RENDER_EXTERNAL_HOSTNAME); '
                'print(settings.CSRF_TRUSTED_ORIGINS)'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('sonica-music-player.onrender.com', result.stdout)
        self.assertIn('https://sonica-music-player.onrender.com', result.stdout)

    def test_render_https_proxy_settings_import_cleanly(self):
        result = self._settings_probe(
            {
                'DEBUG': 'False',
                'SECRET_KEY': PRODUCTION_TEST_SECRET,
                'ALLOWED_HOSTS': 'sonica-music-player.onrender.com',
                'RENDER_EXTERNAL_HOSTNAME': 'sonica-music-player.onrender.com',
                'DATABASE_URL': 'postgresql://sonica:secret-password@db.example.com:5432/sonica',
                'SECURE_SSL_REDIRECT': 'True',
                'SESSION_COOKIE_SECURE': 'True',
                'CSRF_COOKIE_SECURE': 'True',
                'SECURE_HSTS_SECONDS': '0',
                'TRUST_X_FORWARDED_PROTO': 'True',
            },
            (
                'import musicplayer.settings as settings; '
                'print(settings.SECURE_SSL_REDIRECT); '
                'print(settings.SESSION_COOKIE_SECURE); '
                'print(settings.CSRF_COOKIE_SECURE); '
                'print(settings.SECURE_HSTS_SECONDS); '
                'print(settings.SECURE_PROXY_SSL_HEADER)'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("True\nTrue\nTrue\n0\n('HTTP_X_FORWARDED_PROTO', 'https')", result.stdout)

    def test_render_blueprint_uses_safe_configuration(self):
        render_yaml = (PROJECT_ROOT / 'render.yaml').read_text()

        self.assertIn('type: web', render_yaml)
        self.assertIn('runtime: python', render_yaml)
        self.assertIn('name: sonica-postgres', render_yaml)
        self.assertIn('healthCheckPath: /health/', render_yaml)
        self.assertIn('generateValue: true', render_yaml)
        self.assertIn('property: connectionString', render_yaml)
        self.assertIn('bash scripts/render-build.sh', render_yaml)
        self.assertIn('bash scripts/render-start.sh', render_yaml)
        self.assertNotIn('SECRET_KEY=', render_yaml)
        self.assertNotIn('postgresql://', render_yaml)
        self.assertNotIn('disk:', render_yaml)
        self.assertNotIn('*.onrender.com', render_yaml)

    def test_invalid_database_url_fails_clearly_without_credentials(self):
        result = self._settings_probe(
            {
                'DEBUG': 'False',
                'SECRET_KEY': PRODUCTION_TEST_SECRET,
                'ALLOWED_HOSTS': 'example.com',
                'DATABASE_URL': 'not-a-valid-database-url',
            },
            'import musicplayer.settings',
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DATABASE_URL must be a valid database URL', result.stderr)
        self.assertNotIn('not-a-valid-database-url', result.stderr)

    def test_whitenoise_static_file_configuration_is_enabled(self):
        self.assertIn('whitenoise.middleware.WhiteNoiseMiddleware', settings.MIDDLEWARE)
        self.assertEqual(
            settings.STORAGES['staticfiles']['BACKEND'],
            'django.contrib.staticfiles.storage.StaticFilesStorage',
        )

        result = self._settings_probe(
            {
                'DEBUG': 'False',
                'SECRET_KEY': PRODUCTION_TEST_SECRET,
                'ALLOWED_HOSTS': 'example.com',
            },
            'import musicplayer.settings as settings; print(settings.STORAGES["staticfiles"]["BACKEND"])',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            'whitenoise.storage.CompressedManifestStaticFilesStorage',
        )

    def test_static_and_media_paths_are_distinct(self):
        self.assertNotEqual(settings.STATIC_ROOT, settings.MEDIA_ROOT)
        self.assertNotIn(settings.STATIC_ROOT, settings.STATICFILES_DIRS)

    def test_test_runs_use_disposable_media_root(self):
        self.assertNotEqual(settings.MEDIA_ROOT, str(PROJECT_ROOT / 'media'))
        self.assertIn('sonica-test-media', settings.MEDIA_ROOT)

    def test_collectstatic_dry_run_to_disposable_path_leaves_no_output(self):
        temp_static_root = tempfile.mkdtemp()
        shutil.rmtree(temp_static_root)
        out = StringIO()

        try:
            with override_settings(STATIC_ROOT=temp_static_root):
                call_command('collectstatic', '--noinput', '--dry-run', stdout=out)

            self.assertFalse(settings.STATIC_ROOT == temp_static_root)
            self.assertFalse(
                any(temp_static_root in line and 'Copying' in line for line in out.getvalue().splitlines())
            )
        finally:
            shutil.rmtree(temp_static_root, ignore_errors=True)

    def test_no_pending_migrations_in_deployment_ready_baseline(self):
        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])

        self.assertEqual(executor.migration_plan(executor.loader.graph.leaf_nodes()), [])

    @override_settings(
        DEBUG=False,
        SECRET_KEY=PRODUCTION_TEST_SECRET,
        ALLOWED_HOSTS=['example.com'],
        DATABASE_URL='sqlite:///db.sqlite3',
        STORAGES={
            'default': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
            },
            'staticfiles': {
                'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
            },
        },
        CSRF_TRUSTED_ORIGINS=['https://example.com'],
        SECURE_SSL_REDIRECT=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_HSTS_SECONDS=0,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=False,
        SECURE_HSTS_PRELOAD=False,
    )
    def test_deployment_readiness_command_passes_with_safe_production_settings(self):
        out = StringIO()

        call_command('deployment_readiness_check', stdout=out)

        self.assertIn('PASS: deployment readiness checks passed.', out.getvalue())
        self.assertIn('WARN: HSTS is disabled', out.getvalue())
        self.assertIn('WARN: uploaded media needs durable production storage', out.getvalue())

    @override_settings(DEBUG=True)
    def test_deployment_readiness_command_fails_safely_with_invalid_settings(self):
        out = StringIO()
        err = StringIO()

        with self.assertRaises(CommandError):
            call_command('deployment_readiness_check', stdout=out, stderr=err)

        self.assertIn('FAIL:', err.getvalue())
        self.assertNotIn(settings.SECRET_KEY, err.getvalue())

    @override_settings(
        DEBUG=False,
        SECRET_KEY=PRODUCTION_TEST_SECRET,
        ALLOWED_HOSTS=['example.com'],
        CSRF_TRUSTED_ORIGINS=['https://example.com'],
    )
    def test_deployment_readiness_command_requires_database_url_in_production(self):
        err = StringIO()

        with self.assertRaises(CommandError):
            call_command('deployment_readiness_check', stderr=err)

        self.assertIn('DATABASE_URL must be configured for production deployment.', err.getvalue())

    @override_settings(
        DEBUG=False,
        SECRET_KEY=PRODUCTION_TEST_SECRET,
        ALLOWED_HOSTS=['example.com'],
        DATABASE_URL='sqlite:///db.sqlite3',
        STORAGES={
            'default': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
            },
            'staticfiles': {
                'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
            },
        },
        CSRF_TRUSTED_ORIGINS=['https://example.com'],
        SECURE_SSL_REDIRECT=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_HSTS_SECONDS=3600,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True,
    )
    def test_deployment_readiness_command_hides_database_inspection_errors(self):
        err = StringIO()

        with mock.patch(
            'musicapp.management.commands.deployment_readiness_check.MigrationExecutor',
            side_effect=RuntimeError('secret-password'),
        ):
            with self.assertRaises(CommandError):
                call_command('deployment_readiness_check', stderr=err)

        self.assertIn('Database connectivity and migration state must be available.', err.getvalue())
        self.assertNotIn('secret-password', err.getvalue())
