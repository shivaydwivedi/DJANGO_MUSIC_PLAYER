from pathlib import Path

from cloudinary_storage.storage import MediaCloudinaryStorage

from .validators import ALLOWED_AUDIO_EXTENSIONS, ALLOWED_COVER_EXTENSIONS


class SonicaCloudinaryMediaStorage(MediaCloudinaryStorage):
    """Route cover and audio uploads to the correct Cloudinary asset type."""

    def _get_resource_type(self, name):
        extension = Path(name or '').suffix.lower()
        if extension in ALLOWED_AUDIO_EXTENSIONS:
            return 'video'
        if extension in ALLOWED_COVER_EXTENSIONS:
            return 'image'
        return super()._get_resource_type(name)
