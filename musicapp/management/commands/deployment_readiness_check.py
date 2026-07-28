from django.conf import settings
from django.core.checks import run_checks
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor
from django.urls import NoReverseMatch, reverse


class Command(BaseCommand):
    help = 'Run non-destructive platform-neutral deployment readiness checks.'

    def handle(self, *args, **options):
        failures = []
        warnings = []

        if settings.DEBUG:
            failures.append('DEBUG must be False.')
        if not settings.ALLOWED_HOSTS:
            failures.append('ALLOWED_HOSTS must be configured.')
        if not settings.DEBUG and not getattr(settings, 'DATABASE_URL', ''):
            failures.append('DATABASE_URL must be configured for production deployment.')
        if not getattr(settings, 'STATIC_ROOT', None):
            failures.append('STATIC_ROOT must be configured.')
        if not getattr(settings, 'MEDIA_ROOT', None):
            failures.append('MEDIA_ROOT must be configured.')
        if 'whitenoise.middleware.WhiteNoiseMiddleware' not in settings.MIDDLEWARE:
            failures.append('WhiteNoise middleware must be enabled for production static files.')
        static_storage = settings.STORAGES.get('staticfiles', {}).get('BACKEND', '')
        if not settings.DEBUG and static_storage != 'whitenoise.storage.CompressedManifestStaticFilesStorage':
            failures.append('Static files must use WhiteNoise compressed manifest storage.')

        for route_name in ['health', 'ready']:
            try:
                reverse(route_name)
            except NoReverseMatch:
                failures.append('{0} endpoint must resolve.'.format(route_name))

        deploy_issues = run_checks(include_deployment_checks=True)
        if deploy_issues:
            failures.append('Django deployment checks must pass.')

        try:
            connection = connections[DEFAULT_DB_ALIAS]
            database_engine = connection.settings_dict.get('ENGINE', '')
            if getattr(settings, 'DATABASE_URL', '') and database_engine != 'django.db.backends.postgresql':
                warnings.append('DATABASE_URL does not select PostgreSQL; use PostgreSQL for real production.')
            executor = MigrationExecutor(connection)
            pending_plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if pending_plan:
                failures.append('Pending migrations must be applied.')
        except Exception:
            failures.append('Database connectivity and migration state must be available.')

        if failures:
            for failure in failures:
                self.stderr.write('FAIL: {0}'.format(failure))
            raise CommandError('Deployment readiness check failed.')

        for warning in warnings:
            self.stdout.write('WARN: {0}'.format(warning))
        self.stdout.write('WARN: uploaded media needs durable production storage outside the ephemeral app filesystem.')
        self.stdout.write('PASS: deployment readiness checks passed.')
