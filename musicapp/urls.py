from django.urls import path
from . import views

# Add URLConf
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:song_id>/', views.detail, name='detail'),
    path('mymusic/', views.mymusic, name='mymusic'),
    path('playlist/', views.playlist, name='playlist'),
    path('playlist/create/', views.create_playlist, name='create_playlist'),
    path('playlist/<int:playlist_id>/', views.playlist_songs, name='playlist_songs'),
    path('playlist/<int:playlist_id>/rename/', views.rename_playlist, name='rename_playlist'),
    path('playlist/<int:playlist_id>/delete/', views.delete_playlist, name='delete_playlist'),
    path('playlist/<int:playlist_id>/songs/<int:song_id>/add/', views.add_song_to_playlist, name='add_song_to_playlist'),
    path('playlist/<int:playlist_id>/songs/<int:song_id>/remove/', views.remove_song_from_playlist, name='remove_song_from_playlist'),
    path('favourite/', views.favourite, name='favourite'),
    path('songs/<int:song_id>/favourite/add/', views.add_favourite, name='add_favourite'),
    path('songs/<int:song_id>/favourite/remove/', views.remove_favourite, name='remove_favourite'),
    path('all_songs/', views.all_songs, name='all_songs'),
    path('recent/', views.recent, name='recent'),
    path('hindi_songs/', views.hindi_songs, name='hindi_songs'),
    path('english_songs/', views.english_songs, name='english_songs'),
    path('play/<int:song_id>/', views.play_song, name='play_song'),
    path('play_song/<int:song_id>/', views.play_song_index, name='play_song_index'),
    path('play_recent_song/<int:song_id>/', views.play_recent_song, name='play_recent_song'),
    path('songs/<int:song_id>/record-play/', views.record_song_play, name='record_song_play'),

    

]
