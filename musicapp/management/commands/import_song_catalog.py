import csv
import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from musicapp.management.commands.seed_demo_catalog import DEMO_CATALOG_SONGS
from musicapp.models import Favourite, Playlist, PlaylistSong, Recent, Song


REQUIRED_FIELDS = ('name', 'album', 'language', 'year', 'singer', 'audio_filename', 'cover_filename')
FIELD_ALIASES = {
    'audio_filename': ('audio_filename', 'audio filename', 'audio', 'song_file', 'song file'),
    'cover_filename': ('cover_filename', 'cover filename', 'cover', 'song_img', 'song image'),
}


class CatalogEntry:
    def __init__(self, row_number, data, source_dir):
        self.row_number = row_number
        self.name = data['name'].strip()
        self.album = data['album'].strip()
        self.language = data['language'].strip()
        self.year = int(str(data['year']).strip())
        self.singer = data['singer'].strip()
        self.audio_filename = data['audio_filename'].strip()
        self.cover_filename = data['cover_filename'].strip()
        self.audio_path = self._safe_source_path(source_dir, self.audio_filename, 'audio filename')
        self.cover_path = self._safe_source_path(source_dir, self.cover_filename, 'cover filename')

    def metadata(self):
        return {
            'name': self.name,
            'album': self.album,
            'language': self.language,
            'year': self.year,
            'singer': self.singer,
        }

    def lookup(self):
        return {
            'name': self.name,
            'singer': self.singer,
        }

    def _safe_source_path(self, source_dir, filename, label):
        path = Path(filename)
        if path.is_absolute():
            raise CommandError('Row {0}: {1} must be relative to --source.'.format(self.row_number, label))

        source_root = source_dir.resolve()
        candidate = (source_root / path).resolve()
        try:
            candidate.relative_to(source_root)
        except ValueError as exc:
            raise CommandError('Row {0}: {1} must stay inside --source.'.format(self.row_number, label)) from exc
        return candidate


class Command(BaseCommand):
    help = 'Import an authorised song catalog from local files into configured media storage.'

    def add_arguments(self, parser):
        parser.add_argument('--source', help='Directory containing authorised cover and audio files.')
        parser.add_argument('--manifest', help='JSON or CSV catalog manifest.')
        parser.add_argument('--dry-run', action='store_true', help='Validate and preview without database writes.')
        parser.add_argument(
            '--confirm-rights',
            action='store_true',
            help='Confirm you have permission to publish all files in the manifest.',
        )
        parser.add_argument(
            '--remove-demo-catalog',
            action='store_true',
            help='Remove only exact fictional records from seed_demo_catalog.',
        )
        parser.add_argument(
            '--confirm-demo-removal',
            action='store_true',
            help='Confirm removal of exact fictional seed_demo_catalog records.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        remove_demo_catalog = options['remove_demo_catalog']
        imported = self._handle_import(options) if options.get('source') or options.get('manifest') else None

        if imported is None and not remove_demo_catalog:
            raise CommandError('--source and --manifest are required for import.')

        demo_summary = None
        if remove_demo_catalog:
            demo_summary = self._handle_demo_removal(
                dry_run=dry_run,
                confirmed=options['confirm_demo_removal'],
            )

        if imported is None and demo_summary is None:
            raise CommandError('No import or demo-removal action was requested.')

    def _handle_import(self, options):
        if not options.get('source'):
            raise CommandError('--source is required for import.')
        if not options.get('manifest'):
            raise CommandError('--manifest is required for import.')
        if not options['dry_run'] and not options['confirm_rights']:
            raise CommandError(
                'Real imports require --confirm-rights. Confirm that you have permission '
                'to publish every audio and cover file in the manifest.'
            )

        source_dir = Path(options['source'])
        manifest_path = Path(options['manifest'])
        if not source_dir.is_dir():
            raise CommandError('--source must be an existing directory.')
        if not manifest_path.is_file():
            raise CommandError('--manifest must be an existing JSON or CSV file.')

        entries = self._load_manifest(manifest_path, source_dir)
        self._validate_manifest_entries(entries)
        plan = self._build_import_plan(entries)

        if options['dry_run']:
            self._write_plan(plan, prefix='WOULD')
            self.stdout.write(self.style.SUCCESS(
                'Dry run complete: {0} create, {1} update, {2} skip, 0 failed.'.format(
                    len(plan['create']),
                    len(plan['update']),
                    len(plan['skip']),
                )
            ))
            return plan

        summary = {'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        for entry in plan['skip']:
            summary['skipped'] += 1
            self.stdout.write('SKIPPED: {0} - {1}'.format(entry.name, entry.singer))

        for action in ('create', 'update'):
            for entry in plan[action]:
                try:
                    with transaction.atomic():
                        self._save_entry(entry)
                except Exception as exc:
                    summary['failed'] += 1
                    self.stderr.write('FAILED: {0} - {1}: {2}'.format(entry.name, entry.singer, exc))
                else:
                    summary['created' if action == 'create' else 'updated'] += 1
                    self.stdout.write('{0}: {1} - {2}'.format(action.upper() + 'D', entry.name, entry.singer))

        self.stdout.write(self.style.SUCCESS(
            'Import summary: {created} created, {updated} updated, {skipped} skipped, {failed} failed.'.format(
                **summary
            )
        ))
        return summary

    def _load_manifest(self, manifest_path, source_dir):
        suffix = manifest_path.suffix.lower()
        try:
            if suffix == '.json':
                raw = json.loads(manifest_path.read_text(encoding='utf-8'))
                rows = raw.get('songs', raw) if isinstance(raw, dict) else raw
            elif suffix == '.csv':
                with manifest_path.open(newline='', encoding='utf-8') as manifest_file:
                    rows = list(csv.DictReader(manifest_file))
            else:
                raise CommandError('--manifest must be a .json or .csv file.')
        except json.JSONDecodeError as exc:
            raise CommandError('Manifest JSON is invalid: {0}'.format(exc)) from exc

        if not isinstance(rows, list) or not rows:
            raise CommandError('Manifest must contain at least one song row.')

        entries = []
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise CommandError('Row {0}: manifest row must be an object.'.format(index))
            entries.append(CatalogEntry(index, self._normalise_row(row, index), source_dir))
        return entries

    def _normalise_row(self, row, row_number):
        lowered = {str(key).strip().lower(): value for key, value in row.items()}
        normalised = {}
        for field in REQUIRED_FIELDS:
            aliases = FIELD_ALIASES.get(field, (field,))
            value = next((lowered[alias] for alias in aliases if alias in lowered), None)
            if value in (None, ''):
                raise CommandError('Row {0}: missing required field {1}.'.format(row_number, field))
            normalised[field] = str(value)
        try:
            normalised['year'] = int(normalised['year'])
        except ValueError as exc:
            raise CommandError('Row {0}: year must be an integer.'.format(row_number)) from exc
        return normalised

    def _validate_manifest_entries(self, entries):
        names = set()
        for entry in entries:
            if entry.name in names:
                raise CommandError('Manifest contains duplicate song name: {0}.'.format(entry.name))
            names.add(entry.name)

            if entry.language not in dict(Song.Language_Choice):
                raise CommandError('Row {0}: language must be Hindi or English.'.format(entry.row_number))
            if not entry.audio_path.is_file():
                raise CommandError('Row {0}: audio file not found: {1}'.format(entry.row_number, entry.audio_filename))
            if not entry.cover_path.is_file():
                raise CommandError('Row {0}: cover file not found: {1}'.format(entry.row_number, entry.cover_filename))

            with entry.cover_path.open('rb') as cover_file, entry.audio_path.open('rb') as audio_file:
                song = Song(
                    **entry.metadata(),
                    song_img=File(cover_file, name=entry.cover_filename),
                    song_file=File(audio_file, name=entry.audio_filename),
                )
                try:
                    song.full_clean()
                except ValidationError as exc:
                    raise CommandError('Row {0}: {1}'.format(entry.row_number, exc)) from exc

    def _build_import_plan(self, entries):
        plan = {'create': [], 'update': [], 'skip': []}
        for entry in entries:
            same_name = Song.objects.filter(name=entry.name)
            exact = same_name.filter(singer=entry.singer)
            if exact.count() > 1:
                raise CommandError('Conflicting records: multiple songs named {0} by {1}.'.format(
                    entry.name,
                    entry.singer,
                ))
            if same_name.exclude(singer=entry.singer).exists():
                raise CommandError('Conflicting record: song name already exists with another singer: {0}.'.format(
                    entry.name
                ))

            song = exact.first()
            if song is None:
                plan['create'].append(entry)
            elif self._song_matches_entry(song, entry) and song.song_img and song.song_file:
                plan['skip'].append(entry)
            else:
                plan['update'].append(entry)
        return plan

    def _song_matches_entry(self, song, entry):
        metadata = entry.metadata()
        return all(getattr(song, field) == value for field, value in metadata.items())

    def _write_plan(self, plan, prefix):
        for action in ('create', 'update', 'skip'):
            for entry in plan[action]:
                self.stdout.write('{0} {1}: {2} - {3}'.format(
                    prefix,
                    action.upper(),
                    entry.name,
                    entry.singer,
                ))

    def _save_entry(self, entry):
        song = Song.objects.filter(**entry.lookup()).first()
        created = song is None
        if created:
            song = Song(**entry.metadata())
        else:
            for field, value in entry.metadata().items():
                setattr(song, field, value)

        with entry.cover_path.open('rb') as cover_file, entry.audio_path.open('rb') as audio_file:
            if created or not song.song_img:
                song.song_img.save(entry.cover_filename, File(cover_file), save=False)
            if created or not song.song_file:
                song.song_file.save(entry.audio_filename, File(audio_file), save=False)
            song.full_clean()
            song.save()

    def _handle_demo_removal(self, dry_run, confirmed):
        if not dry_run and not confirmed:
            raise CommandError('--confirm-demo-removal is required with --remove-demo-catalog.')

        demo_songs = Song.objects.filter(self._exact_demo_catalog_query()).order_by('id')
        removable = []
        blocked = []
        for song in demo_songs:
            if self._has_relationships(song):
                blocked.append(song)
            else:
                removable.append(song)

        for song in removable:
            self.stdout.write('{0}: {1} - {2}'.format('WOULD REMOVE' if dry_run else 'REMOVED', song.name, song.singer))
        for song in blocked:
            self.stdout.write('SKIPPED RELATED: {0} - {1}'.format(song.name, song.singer))

        if not dry_run and removable:
            Song.objects.filter(id__in=[song.id for song in removable]).delete()

        self.stdout.write(self.style.SUCCESS(
            'Demo removal summary: {0} removed, {1} skipped with relationships.'.format(
                0 if dry_run else len(removable),
                len(blocked),
            )
        ))
        return {'removed': 0 if dry_run else len(removable), 'blocked': len(blocked)}

    def _exact_demo_catalog_query(self):
        query = Q()
        for demo_song in DEMO_CATALOG_SONGS:
            query |= Q(
                name=demo_song['name'],
                album=demo_song['album'],
                language=demo_song['language'],
                year=demo_song['year'],
                singer=demo_song['singer'],
            )
        return query

    def _has_relationships(self, song):
        return (
            Favourite.objects.filter(song=song).exists()
            or Recent.objects.filter(song=song).exists()
            or Playlist.objects.filter(song=song).exists()
            or PlaylistSong.objects.filter(song=song).exists()
        )
