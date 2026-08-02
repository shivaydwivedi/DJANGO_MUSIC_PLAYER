from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile


ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a'}
ALLOWED_COVER_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
DEFAULT_MAX_AUDIO_UPLOAD_SIZE = 20 * 1024 * 1024
DEFAULT_MAX_COVER_UPLOAD_SIZE = 5 * 1024 * 1024


def _extension(filename):
    return Path(filename or '').suffix.lower()


def _max_size(setting_name, default):
    return getattr(settings, setting_name, default)


def _is_committed_field_file(value):
    return isinstance(value, FieldFile) and value._committed


def _validate_upload(value, *, allowed_extensions, max_size, label):
    if not value:
        return
    if _is_committed_field_file(value):
        return

    extension = _extension(getattr(value, 'name', ''))
    if extension not in allowed_extensions:
        allowed = ', '.join(sorted(allowed_extensions))
        raise ValidationError(
            '{label} must use one of these file extensions: {allowed}.'.format(
                label=label,
                allowed=allowed,
            )
        )

    size = getattr(value, 'size', None)
    if size is not None and size > max_size:
        raise ValidationError(
            '{label} must be {limit_mb:g} MB or smaller.'.format(
                label=label,
                limit_mb=max_size / (1024 * 1024),
            )
        )


def validate_song_audio_upload(value):
    _validate_upload(
        value,
        allowed_extensions=ALLOWED_AUDIO_EXTENSIONS,
        max_size=_max_size('SONICA_MAX_AUDIO_UPLOAD_SIZE', DEFAULT_MAX_AUDIO_UPLOAD_SIZE),
        label='Song audio',
    )


def validate_song_cover_upload(value):
    _validate_upload(
        value,
        allowed_extensions=ALLOWED_COVER_EXTENSIONS,
        max_size=_max_size('SONICA_MAX_COVER_UPLOAD_SIZE', DEFAULT_MAX_COVER_UPLOAD_SIZE),
        label='Song cover',
    )
