from django.apps import AppConfig


class MusicappConfig(AppConfig):
    name = 'musicapp'

    def ready(self):
        from django.conf import settings

        if not getattr(settings, 'CONFIGURE_CLOUDINARY_FIELD_STORAGE', False):
            return

        from .models import Song
        from .storage import SonicaCloudinaryAudioStorage, SonicaCloudinaryImageStorage

        Song._meta.get_field('song_img').storage = SonicaCloudinaryImageStorage()
        Song._meta.get_field('song_file').storage = SonicaCloudinaryAudioStorage()
