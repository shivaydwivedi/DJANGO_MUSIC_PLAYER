from django.core.management.base import BaseCommand
from django.db.models import Q

from musicapp.models import Song


DEMO_CATALOG_SONGS = [
    {
        'name': 'Neon Courtyard',
        'album': 'Midnight Metro',
        'language': 'English',
        'year': 2026,
        'singer': 'Aria Vale',
    },
    {
        'name': 'Paper Lantern Sky',
        'album': 'Letters From Dawn',
        'language': 'English',
        'year': 2025,
        'singer': 'Milo Crest',
    },
    {
        'name': 'Harbor Lights Awake',
        'album': 'North Pier Stories',
        'language': 'English',
        'year': 2026,
        'singer': 'June Halley',
    },
    {
        'name': 'Velvet Rain Parade',
        'album': 'Small Hours Radio',
        'language': 'English',
        'year': 2024,
        'singer': 'The Luma Room',
    },
    {
        'name': 'Chand Ki Raah',
        'album': 'Sheher Ke Rang',
        'language': 'Hindi',
        'year': 2026,
        'singer': 'Aarav Mehta',
    },
    {
        'name': 'Rangon Ki Dhoop',
        'album': 'Sheher Ke Rang',
        'language': 'Hindi',
        'year': 2025,
        'singer': 'Naina Verma',
    },
    {
        'name': 'Savera Saath Chale',
        'album': 'Nayi Subah',
        'language': 'Hindi',
        'year': 2026,
        'singer': 'Kabir Anand',
    },
    {
        'name': 'Mehfil Mein Badal',
        'album': 'Raag Aangan',
        'language': 'Hindi',
        'year': 2024,
        'singer': 'Tara Sethi',
    },
]


def seeded_catalog_query():
    query = Q()
    for demo_song in DEMO_CATALOG_SONGS:
        query |= Q(name=demo_song['name'], singer=demo_song['singer'])
    return query


class Command(BaseCommand):
    help = 'Seed a production-safe fictional Sonica demo catalog without media files.'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        skipped = 0

        for demo_song in DEMO_CATALOG_SONGS:
            lookup = {
                'name': demo_song['name'],
                'singer': demo_song['singer'],
            }
            existing_song = Song.objects.filter(**lookup).order_by('id').first()

            if existing_song is None:
                Song.objects.create(**demo_song)
                created += 1
                continue

            changed_fields = []
            for field in ('album', 'language', 'year'):
                if getattr(existing_song, field) != demo_song[field]:
                    setattr(existing_song, field, demo_song[field])
                    changed_fields.append(field)

            if changed_fields:
                existing_song.save(update_fields=changed_fields)
                updated += 1
            else:
                skipped += 1

        seeded_catalog = Song.objects.filter(seeded_catalog_query())
        hindi_total = seeded_catalog.filter(language='Hindi').count()
        english_total = seeded_catalog.filter(language='English').count()

        self.stdout.write(self.style.SUCCESS(
            'Sonica demo catalog: {0} created, {1} updated, {2} skipped.'.format(
                created,
                updated,
                skipped,
            )
        ))
        self.stdout.write(self.style.SUCCESS(
            'Final catalogue totals: {0} songs ({1} Hindi, {2} English).'.format(
                seeded_catalog.count(),
                hindi_total,
                english_total,
            )
        ))
