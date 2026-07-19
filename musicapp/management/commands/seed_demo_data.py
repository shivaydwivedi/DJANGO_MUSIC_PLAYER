from django.core.management.base import BaseCommand

from musicapp.models import Song


DEMO_ALBUM = 'Sonica Demo Sessions'

DEMO_SONGS = [
    {
        'name': 'Crimson Echo',
        'album': DEMO_ALBUM,
        'language': 'English',
        'year': 2026,
        'singer': 'Ari Vale',
    },
    {
        'name': 'Midnight Signal',
        'album': DEMO_ALBUM,
        'language': 'English',
        'year': 2025,
        'singer': 'Nova Lane',
    },
    {
        'name': 'City of Static',
        'album': DEMO_ALBUM,
        'language': 'English',
        'year': 2024,
        'singer': 'Mira Knox',
    },
    {
        'name': 'Velvet Frequency',
        'album': DEMO_ALBUM,
        'language': 'English',
        'year': 2026,
        'singer': 'Iris North',
    },
    {
        'name': 'Dil Ki Dhoop',
        'album': DEMO_ALBUM,
        'language': 'Hindi',
        'year': 2026,
        'singer': 'Revaan Noor',
    },
    {
        'name': 'Raat Ka Safar',
        'album': DEMO_ALBUM,
        'language': 'Hindi',
        'year': 2025,
        'singer': 'Kavya Sen',
    },
    {
        'name': 'Nayi Dhadkan',
        'album': DEMO_ALBUM,
        'language': 'Hindi',
        'year': 2024,
        'singer': 'Ahan Verma',
    },
    {
        'name': 'Shehar Ki Roshni',
        'album': DEMO_ALBUM,
        'language': 'Hindi',
        'year': 2026,
        'singer': 'Tara Iqbal',
    },
]


class Command(BaseCommand):
    help = 'Seed or clear a small fictional Sonica demo catalog without media files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete only demo rows created by this command.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = Song.objects.filter(
                album=DEMO_ALBUM,
                name__in=[song['name'] for song in DEMO_SONGS],
            ).delete()
            self.stdout.write(self.style.SUCCESS(
                'Cleared {0} Sonica demo song rows.'.format(deleted)
            ))
            return

        created = 0
        updated = 0
        unchanged = 0

        for demo_song in DEMO_SONGS:
            song, was_created = Song.objects.get_or_create(
                name=demo_song['name'],
                album=DEMO_ALBUM,
                defaults=demo_song,
            )

            if was_created:
                created += 1
                continue

            changed = False
            for field in ('language', 'year', 'singer'):
                if getattr(song, field) != demo_song[field]:
                    setattr(song, field, demo_song[field])
                    changed = True

            if song.song_img or song.song_file:
                song.song_img = ''
                song.song_file = ''
                changed = True

            if changed:
                song.save(update_fields=['language', 'year', 'singer', 'song_img', 'song_file'])
                updated += 1
            else:
                unchanged += 1

        self.stdout.write(self.style.SUCCESS(
            'Sonica demo songs: {0} created, {1} updated, {2} unchanged.'.format(
                created,
                updated,
                unchanged,
            )
        ))
