from django.contrib import admin
from .models import *

# Register your models here.

class LegacyPlaylistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'playlist_name', 'song')
    search_fields = ('playlist_name', 'user__username', 'song__name')
    list_filter = ('user',)


class PlaylistContainerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'song_count', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)

    def song_count(self, obj):
        return obj.songs.count()


class PlaylistSongAdmin(admin.ModelAdmin):
    list_display = ('id', 'playlist', 'song', 'added_at')
    search_fields = ('playlist__name', 'playlist__user__username', 'song__name')
    list_filter = ('playlist__user',)


admin.site.register(Song)
admin.site.register(Playlist, LegacyPlaylistAdmin)
admin.site.register(PlaylistContainer, PlaylistContainerAdmin)
admin.site.register(PlaylistSong, PlaylistSongAdmin)
admin.site.register(Favourite)
admin.site.register(Recent)
