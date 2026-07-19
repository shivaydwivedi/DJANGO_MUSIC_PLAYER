import shutil
import tempfile
from io import StringIO
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
    def test_wsgi_application_imports_successfully(self):
        from musicplayer.wsgi import application

        self.assertTrue(callable(application))

    def test_waitress_server_imports_successfully(self):
        import waitress

        self.assertTrue(hasattr(waitress, 'serve'))

    def test_static_and_media_paths_are_distinct(self):
        self.assertNotEqual(settings.STATIC_ROOT, settings.MEDIA_ROOT)
        self.assertNotIn(settings.STATIC_ROOT, settings.STATICFILES_DIRS)

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
        CSRF_TRUSTED_ORIGINS=['https://example.com'],
        SECURE_SSL_REDIRECT=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_HSTS_SECONDS=3600,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True,
    )
    def test_deployment_readiness_command_passes_with_safe_production_settings(self):
        out = StringIO()

        call_command('deployment_readiness_check', stdout=out)

        self.assertIn('PASS: deployment readiness checks passed.', out.getvalue())

    @override_settings(DEBUG=True)
    def test_deployment_readiness_command_fails_safely_with_invalid_settings(self):
        out = StringIO()
        err = StringIO()

        with self.assertRaises(CommandError):
            call_command('deployment_readiness_check', stdout=out, stderr=err)

        self.assertIn('FAIL:', err.getvalue())
        self.assertNotIn(settings.SECRET_KEY, err.getvalue())
