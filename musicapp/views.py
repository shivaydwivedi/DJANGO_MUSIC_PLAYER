from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from authentication.compat import get_safe_redirect_url


# Create your views here.
def _get_last_played_song(user):
    if user.is_anonymous:
        return None

    last_recent = Recent.objects.filter(user=user).select_related('song').order_by('-id').first()
    if last_recent:
        return last_recent.song
    return None


def _record_recent_play(user, song):
    with transaction.atomic():
        Recent.objects.filter(user=user, song=song).delete()
        return Recent.objects.create(user=user, song=song)


def _get_recent_songs(user, limit=None):
    if user.is_anonymous:
        return []

    recent_ids = []
    seen_song_ids = set()
    rows = Recent.objects.filter(user=user).values_list('song_id', flat=True).order_by('-id')
    for song_id in rows:
        if song_id in seen_song_ids:
            continue
        seen_song_ids.add(song_id)
        recent_ids.append(song_id)
        if limit is not None and len(recent_ids) >= limit:
            break

    songs_by_id = Song.objects.in_bulk(recent_ids)
    return [songs_by_id[song_id] for song_id in recent_ids if song_id in songs_by_id]


def _get_valid_playlist_name(request):
    playlist_name = request.POST.get('playlist_name', '').strip()
    if not playlist_name:
        return None, "Missing playlist name."

    max_length = PlaylistContainer._meta.get_field('name').max_length
    if max_length is not None and len(playlist_name) > max_length:
        return None, "Playlist name is too long."

    return playlist_name, None


def _get_user_playlist_or_404(user, playlist_id):
    return get_object_or_404(
        PlaylistContainer.objects.filter(user=user),
        id=playlist_id,
    )


def _redirect_to_next_or(request, fallback_name, **fallback_kwargs):
    next_url = get_safe_redirect_url(request)
    if next_url:
        return redirect(next_url)
    return redirect(fallback_name, **fallback_kwargs)


def _activate_favourite(user, song):
    with transaction.atomic():
        favourites = list(
            Favourite.objects
            .select_for_update()
            .filter(user=user, song=song)
            .order_by('-is_fav', 'id')
        )
        if not favourites:
            Favourite.objects.create(user=user, song=song, is_fav=True)
            return

        favourite = favourites[0]
        if not favourite.is_fav:
            favourite.is_fav = True
            favourite.save(update_fields=['is_fav'])

        duplicate_ids = [row.id for row in favourites[1:]]
        if duplicate_ids:
            Favourite.objects.filter(id__in=duplicate_ids).delete()


def index(request):

    #Display recent songs
    if not request.user.is_anonymous :
        recent_songs = _get_recent_songs(request.user, limit=5)
    else:
        recent_songs = None

    last_played_song = _get_last_played_song(request.user)
    first_time = last_played_song is None

    #Display all songs
    songs = Song.objects.all()

    #Display few songs on home page
    songs_all = list(Song.objects.all().values('id').order_by('?'))
    sliced_ids = [each['id'] for each in songs_all][:5]
    indexpage_songs = Song.objects.filter(id__in=sliced_ids)

    # Display Hindi Songs
    songs_hindi = list(Song.objects.filter(language='Hindi').values('id'))
    sliced_ids = [each['id'] for each in songs_hindi][:5]
    indexpage_hindi_songs = Song.objects.filter(id__in=sliced_ids)

    # Display English Songs
    songs_english = list(Song.objects.filter(language='English').values('id'))
    sliced_ids = [each['id'] for each in songs_english][:5]
    indexpage_english_songs = Song.objects.filter(id__in=sliced_ids)

    if len(request.GET) > 0:
        search_query = request.GET.get('q') or ''
        filtered_songs = songs.filter(Q(name__icontains=search_query)).distinct()
        context = {'all_songs': filtered_songs,'last_played':last_played_song,'query_search':True}
        return render(request, 'musicapp/index.html', context)

    context = {
        'all_songs':indexpage_songs,
        'recent_songs': recent_songs,
        'hindi_songs':indexpage_hindi_songs,
        'english_songs':indexpage_english_songs,
        'last_played':last_played_song,
        'first_time': first_time,
        'query_search':False,
    }
    return render(request, 'musicapp/index.html', context=context)


def hindi_songs(request):

    hindi_songs = Song.objects.filter(language='Hindi')

    last_played_song = _get_last_played_song(request.user)

    query = request.GET.get('q')

    if query:
        hindi_songs = Song.objects.filter(Q(name__icontains=query)).distinct()
        context = {'hindi_songs': hindi_songs,'last_played':last_played_song}
        return render(request, 'musicapp/hindi_songs.html', context)

    context = {'hindi_songs':hindi_songs,'last_played':last_played_song}
    return render(request, 'musicapp/hindi_songs.html',context=context)


def english_songs(request):

    english_songs = Song.objects.filter(language='English')

    last_played_song = _get_last_played_song(request.user)

    query = request.GET.get('q')

    if query:
        english_songs = Song.objects.filter(Q(name__icontains=query)).distinct()
        context = {'english_songs': english_songs,'last_played':last_played_song}
        return render(request, 'musicapp/english_songs.html', context)

    context = {'english_songs':english_songs,'last_played':last_played_song}
    return render(request, 'musicapp/english_songs.html',context=context)

@login_required(login_url='login')
def play_song(request, song_id):
    get_object_or_404(Song, id=song_id)
    return redirect('all_songs')


@login_required(login_url='login')
def play_song_index(request, song_id):
    get_object_or_404(Song, id=song_id)
    return redirect('index')

@login_required(login_url='login')
def play_recent_song(request, song_id):
    get_object_or_404(Song, id=song_id)
    return redirect('recent')


@login_required(login_url='login')
@require_POST
def record_song_play(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    _record_recent_play(request.user, song)
    return _redirect_to_next_or(request, 'detail', song_id=song.id)


def all_songs(request):
    songs = Song.objects.all()

    last_played_song = _get_last_played_song(request.user)
    first_time = last_played_song is None

    
    # apply search filters
    qs_singers = Song.objects.values_list('singer').all()
    s_list = [s.split(',') for singer in qs_singers for s in singer]
    all_singers = sorted(list(set([s.strip() for singer in s_list for s in singer])))
    qs_languages = Song.objects.values_list('language').all()
    all_languages = sorted(list(set([l.strip() for lang in qs_languages for l in lang])))
    
    if len(request.GET) > 0:
        search_query = request.GET.get('q') or ''
        search_singer = request.GET.get('singers') or ''
        search_language = request.GET.get('languages') or ''
        filtered_songs = songs.filter(Q(name__icontains=search_query)).filter(Q(language__icontains=search_language)).filter(Q(singer__icontains=search_singer)).distinct()
        context = {
        'songs': filtered_songs,
        'last_played':last_played_song,
        'all_singers': all_singers,
        'all_languages': all_languages,
        'query_search': True,
        }
        return render(request, 'musicapp/all_songs.html', context)

    context = {
        'songs': songs,
        'last_played':last_played_song,
        'first_time':first_time,
        'all_singers': all_singers,
        'all_languages': all_languages,
        'query_search' : False,
        }
    return render(request, 'musicapp/all_songs.html', context=context)


def recent(request):
    
    last_played_song = _get_last_played_song(request.user)

    #Display recent songs
    recent_songs = _get_recent_songs(request.user)

    if len(request.GET) > 0:
        search_query = request.GET.get('q') or ''
        filtered_songs = [
            song for song in recent_songs
            if search_query.lower() in song.name.lower()
        ]
        context = {'recent_songs': filtered_songs,'last_played':last_played_song,'query_search':True}
        return render(request, 'musicapp/recent.html', context)

    context = {'recent_songs':recent_songs,'last_played':last_played_song,'query_search':False}
    return render(request, 'musicapp/recent.html', context=context)


@login_required(login_url='login')
def detail(request, song_id):
    songs = get_object_or_404(Song, id=song_id)

    last_played_song = _get_last_played_song(request.user)


    playlists = PlaylistContainer.objects.filter(user=request.user).annotate(song_count=Count('songs'))
    is_favourite = Favourite.objects.filter(user=request.user, song=songs, is_fav=True).exists()

    if request.method == "POST":
        if 'playlist_action' in request.POST:
            return HttpResponseBadRequest("Invalid playlist action.")
        if 'favorite_action' in request.POST:
            return HttpResponseBadRequest("Invalid favourite action.")

    context = {'songs': songs, 'playlists': playlists, 'is_favourite': is_favourite,'last_played':last_played_song}
    return render(request, 'musicapp/detail.html', context=context)


@login_required(login_url='login')
def mymusic(request):
    return render(request, 'musicapp/mymusic.html')


@login_required(login_url='login')
def playlist(request):
    playlists = PlaylistContainer.objects.filter(user=request.user).annotate(song_count=Count('songs'))
    context = {'playlists': playlists}
    return render(request, 'musicapp/playlist.html', context=context)


@login_required(login_url='login')
def playlist_songs(request, playlist_id):
    playlist_obj = _get_user_playlist_or_404(request.user, playlist_id)
    memberships = (
        PlaylistSong.objects
        .filter(playlist=playlist_obj)
        .select_related('song')
        .order_by('added_at', 'id')
    )
    songs = [membership.song for membership in memberships]
    context = {'playlist': playlist_obj, 'songs': songs}

    return render(request, 'musicapp/playlist_songs.html', context=context)


@login_required(login_url='login')
@require_POST
def create_playlist(request):
    playlist_name, error = _get_valid_playlist_name(request)
    if error:
        return HttpResponseBadRequest(error)
    if PlaylistContainer.objects.filter(user=request.user, name=playlist_name).exists():
        return HttpResponseBadRequest("A playlist with that name already exists.")
    try:
        with transaction.atomic():
            PlaylistContainer.objects.create(
                user=request.user,
                name=playlist_name,
            )
    except IntegrityError:
        return HttpResponseBadRequest("A playlist with that name already exists.")
    messages.success(request, "Playlist created.")
    return redirect('playlist')


@login_required(login_url='login')
@require_POST
def rename_playlist(request, playlist_id):
    playlist_obj = _get_user_playlist_or_404(request.user, playlist_id)
    playlist_name, error = _get_valid_playlist_name(request)
    if error:
        return HttpResponseBadRequest(error)
    if PlaylistContainer.objects.filter(user=request.user, name=playlist_name).exclude(id=playlist_obj.id).exists():
        return HttpResponseBadRequest("A playlist with that name already exists.")
    playlist_obj.name = playlist_name
    try:
        with transaction.atomic():
            playlist_obj.save(update_fields=['name', 'updated_at'])
    except IntegrityError:
        return HttpResponseBadRequest("A playlist with that name already exists.")
    messages.success(request, "Playlist renamed.")
    return redirect('playlist_songs', playlist_id=playlist_obj.id)


@login_required(login_url='login')
@require_POST
def delete_playlist(request, playlist_id):
    playlist_obj = _get_user_playlist_or_404(request.user, playlist_id)
    playlist_obj.delete()
    messages.success(request, "Playlist deleted.")
    return redirect('playlist')


@login_required(login_url='login')
@require_POST
def add_song_to_playlist(request, playlist_id, song_id):
    playlist_obj = _get_user_playlist_or_404(request.user, playlist_id)
    song = get_object_or_404(Song, id=song_id)
    with transaction.atomic():
        _membership, created = PlaylistSong.objects.get_or_create(playlist=playlist_obj, song=song)
    if created:
        messages.success(request, "Song added to playlist.")
    else:
        messages.info(request, "That song is already in this playlist.")
    return redirect('detail', song_id=song.id)


@login_required(login_url='login')
@require_POST
def remove_song_from_playlist(request, playlist_id, song_id):
    playlist_obj = _get_user_playlist_or_404(request.user, playlist_id)
    get_object_or_404(Song, id=song_id)
    PlaylistSong.objects.filter(playlist=playlist_obj, song_id=song_id).delete()
    messages.success(request, "Song removed from playlist.")
    return redirect('playlist_songs', playlist_id=playlist_obj.id)


@login_required(login_url='login')
@require_POST
def add_favourite(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    _activate_favourite(request.user, song)
    messages.success(request, "Added to favorite!")
    return _redirect_to_next_or(request, 'detail', song_id=song.id)


@login_required(login_url='login')
@require_POST
def remove_favourite(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    Favourite.objects.filter(user=request.user, song=song).delete()
    messages.success(request, "Removed from favourite!")
    return _redirect_to_next_or(request, 'favourite')


@login_required(login_url='login')
def favourite(request):
    songs = Song.objects.filter(favourite__user=request.user, favourite__is_fav=True).distinct()
    context = {'songs': songs}
    return render(request, 'musicapp/favourite.html', context=context)
