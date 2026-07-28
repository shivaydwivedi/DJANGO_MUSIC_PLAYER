from musicapp.management.commands.project_smoke_test import Command as ProjectSmokeCommand


class Command(ProjectSmokeCommand):
    help = 'Deprecated alias for project_smoke_test.'
