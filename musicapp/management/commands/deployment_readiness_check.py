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

        if settings.DEBUG:
            failures.append('DEBUG must be False.')
        if not settings.ALLOWED_HOSTS:
            failures.append('ALLOWED_HOSTS must be configured.')
        if not getattr(settings, 'STATIC_ROOT', None):
            failures.append('STATIC_ROOT must be configured.')
        if not getattr(settings, 'MEDIA_ROOT', None):
            failures.append('MEDIA_ROOT must be configured.')

        for route_name in ['health', 'ready']:
            try:
                reverse(route_name)
            except NoReverseMatch:
                failures.append('{0} endpoint must resolve.'.format(route_name))

        deploy_issues = run_checks(include_deployment_checks=True)
        if deploy_issues:
            failures.append('Django deployment checks must pass.')

        connection = connections[DEFAULT_DB_ALIAS]
        executor = MigrationExecutor(connection)
        pending_plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if pending_plan:
            failures.append('Pending migrations must be applied.')

        if failures:
            for failure in failures:
                self.stderr.write('FAIL: {0}'.format(failure))
            raise CommandError('Deployment readiness check failed.')

        self.stdout.write('PASS: deployment readiness checks passed.')
