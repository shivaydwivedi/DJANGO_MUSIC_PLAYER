from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from .validators import validate_song_audio_upload, validate_song_cover_upload


def _song_image_storage_options():
    if not getattr(settings, 'CONFIGURE_CLOUDINARY_FIELD_STORAGE', False):
        return {}
    from .storage import SonicaCloudinaryImageStorage
    return {'storage': SonicaCloudinaryImageStorage()}


def _song_audio_storage_options():
    if not getattr(settings, 'CONFIGURE_CLOUDINARY_FIELD_STORAGE', False):
        return {}
    from .storage import SonicaCloudinaryAudioStorage
    return {'storage': SonicaCloudinaryAudioStorage()}


# Create your models here.
class Song(models.Model):

    Language_Choice = (
              ('Hindi', 'Hindi'),
              ('English', 'English'),
          )

    name = models.CharField(max_length=200)
    album = models.CharField(max_length=200)
    language = models.CharField(max_length=20,choices=Language_Choice,default='Hindi')
    song_img = models.FileField(blank=True, **_song_image_storage_options())
    year = models.IntegerField()
    singer = models.CharField(max_length=200)
    song_file = models.FileField(blank=True, **_song_audio_storage_options())

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        validate_song_cover_upload(self.song_img)
        validate_song_audio_upload(self.song_file)


class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    playlist_name = models.CharField(max_length=200)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)


class PlaylistContainer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlist_containers')
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='uniq_pl_container_user_name'),
        ]
        indexes = [
            models.Index(fields=['user', 'name'], name='pl_container_user_name_idx'),
        ]
        ordering = ['name', 'id']

    def __str__(self):
        return self.name


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(PlaylistContainer, on_delete=models.CASCADE, related_name='songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='playlist_memberships')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['playlist', 'song'], name='uniq_pl_song_membership'),
        ]
        indexes = [
            models.Index(fields=['playlist', 'added_at'], name='pl_song_added_idx'),
        ]
        ordering = ['added_at', 'id']

    def __str__(self):
        return '{0} - {1}'.format(self.playlist, self.song)


class Favourite(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    is_fav = models.BooleanField(default=False)


class Recent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
