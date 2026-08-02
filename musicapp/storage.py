from cloudinary_storage.storage import MediaCloudinaryStorage, VideoMediaCloudinaryStorage


class SonicaCloudinaryImageStorage(MediaCloudinaryStorage):
    """Store and deliver Sonica cover images as Cloudinary image resources."""


class SonicaCloudinaryAudioStorage(VideoMediaCloudinaryStorage):
    """Store and deliver Sonica audio as Cloudinary video resources."""


SonicaCloudinaryMediaStorage = SonicaCloudinaryImageStorage
