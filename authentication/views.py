from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from allauth.socialaccount.models import SocialApp
from musicapp.models import Favourite, PlaylistContainer, PlaylistSong, Recent
from .compat import get_safe_redirect_url
from .forms import UserLoginForm, ProfileUpdateForm, RegistrationForm


# Create your views here.
def _is_google_auth_configured():
    return (
        settings.ENABLE_GOOGLE_AUTH and
        SocialApp.objects.filter(provider='google').exists()
    )


def login_request(request):
    if request.user.is_authenticated:
        return redirect(get_safe_redirect_url(request) or 'index')

    title = "Login"
    form = UserLoginForm(request.POST or None)
    next_url = get_safe_redirect_url(request)
    context = {
        'form': form,
        'title': title,
        'next': next_url,
        'google_auth_configured': _is_google_auth_configured(),
    }
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=username, password=password)

        login(request, user)
        # messages.info(request, f"You are now logged in  as {user}")
        return redirect(next_url or settings.LOGIN_REDIRECT_URL)
    return render(request, 'authentication/login.html', context=context)


def signup_request(request):
    title = "Create Account"
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()

    context = {
        'form': form,
        'title': title,
        'google_auth_configured': _is_google_auth_configured(),
    }
    return render(request, 'authentication/signup.html', context=context)


@login_required(login_url='login')
def profile_request(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user, user=request.user)

    user = request.user
    recent_activity = Recent.objects.filter(user=user).select_related('song').order_by('-id')[:5]
    username = user.username.strip()
    initials = ''.join(part[0] for part in username.split()[:2]).upper() or username[:1].upper() or 'S'

    context = {
        'form': form,
        'initials': initials[:2],
        'favourite_count': Favourite.objects.filter(user=user, is_fav=True).count(),
        'playlist_count': PlaylistContainer.objects.filter(user=user).count(),
        'recent_count': Recent.objects.filter(user=user).count(),
        'playlist_row_count': PlaylistSong.objects.filter(playlist__user=user).count(),
        'recent_activity': recent_activity,
    }
    return render(request, 'authentication/profile.html', context=context)


@require_POST
def logout_request(request):
    logout(request)
    # messages.info(request, "Logged out successfully!")
    return redirect('index')
