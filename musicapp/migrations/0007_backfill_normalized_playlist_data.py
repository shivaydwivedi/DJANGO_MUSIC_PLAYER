from django.db import migrations


PROVENANCE_TABLE = 'musicapp_playlist_data_migration_0007'


def create_provenance_table(schema_editor):
    schema_editor.execute(
        """
        CREATE TABLE IF NOT EXISTS musicapp_playlist_data_migration_0007 (
            user_id integer NOT NULL,
            playlist_name varchar(200) NOT NULL,
            song_id integer NOT NULL,
            container_id integer NOT NULL,
            membership_id integer NOT NULL,
            created_container integer NOT NULL,
            created_membership integer NOT NULL,
            PRIMARY KEY (user_id, playlist_name, song_id)
        )
        """
    )


def drop_provenance_table(schema_editor):
    schema_editor.execute('DROP TABLE IF EXISTS musicapp_playlist_data_migration_0007')


def provenance_exists(schema_editor, user_id, playlist_name, song_id):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM musicapp_playlist_data_migration_0007
            WHERE user_id = %s AND playlist_name = %s AND song_id = %s
            """,
            [user_id, playlist_name, song_id],
        )
        return cursor.fetchone() is not None


def record_provenance(
    schema_editor,
    user_id,
    playlist_name,
    song_id,
    container_id,
    membership_id,
    created_container,
    created_membership,
):
    if provenance_exists(schema_editor, user_id, playlist_name, song_id):
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO musicapp_playlist_data_migration_0007 (
                user_id,
                playlist_name,
                song_id,
                container_id,
                membership_id,
                created_container,
                created_membership
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            [
                user_id,
                playlist_name,
                song_id,
                container_id,
                membership_id,
                int(created_container),
                int(created_membership),
            ],
        )


def get_provenance_rows(schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, playlist_name, song_id, container_id, membership_id,
                   created_container, created_membership
            FROM musicapp_playlist_data_migration_0007
            ORDER BY user_id, playlist_name, song_id
            """
        )
        return cursor.fetchall()


def forwards(apps, schema_editor):
    Playlist = apps.get_model('musicapp', 'Playlist')
    PlaylistContainer = apps.get_model('musicapp', 'PlaylistContainer')
    PlaylistSong = apps.get_model('musicapp', 'PlaylistSong')

    create_provenance_table(schema_editor)

    legacy_memberships = (
        Playlist.objects
        .values('user_id', 'playlist_name', 'song_id')
        .distinct()
        .order_by('user_id', 'playlist_name', 'song_id')
    )

    for legacy_membership in legacy_memberships.iterator():
        user_id = legacy_membership['user_id']
        playlist_name = legacy_membership['playlist_name']
        song_id = legacy_membership['song_id']

        container, created_container = PlaylistContainer.objects.get_or_create(
            user_id=user_id,
            name=playlist_name,
        )
        membership, created_membership = PlaylistSong.objects.get_or_create(
            playlist=container,
            song_id=song_id,
        )
        record_provenance(
            schema_editor,
            user_id,
            playlist_name,
            song_id,
            container.id,
            membership.id,
            created_container,
            created_membership,
        )


def backwards(apps, schema_editor):
    PlaylistContainer = apps.get_model('musicapp', 'PlaylistContainer')
    PlaylistSong = apps.get_model('musicapp', 'PlaylistSong')

    create_provenance_table(schema_editor)

    created_container_ids = set()
    for row in get_provenance_rows(schema_editor):
        _user_id, _playlist_name, _song_id, container_id, membership_id, created_container, created_membership = row
        if created_membership:
            PlaylistSong.objects.filter(id=membership_id).delete()
        if created_container:
            created_container_ids.add(container_id)

    for container_id in sorted(created_container_ids):
        if not PlaylistSong.objects.filter(playlist_id=container_id).exists():
            PlaylistContainer.objects.filter(id=container_id).delete()

    drop_provenance_table(schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('musicapp', '0006_playlistcontainer_playlistsong_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
