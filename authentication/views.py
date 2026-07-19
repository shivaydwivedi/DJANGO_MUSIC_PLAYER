from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.utils.http import is_safe_url
from allauth.socialaccount.models import SocialApp
from .forms import UserLoginForm, RegistrationForm


# Create your views here.
def _is_google_auth_configured():
    return (
        settings.ENABLE_GOOGLE_AUTH and
        SocialApp.objects.filter(provider='google').exists()
    )


def _get_safe_redirect_url(request):
    redirect_to = request.POST.get('next') or request.GET.get('next')
    if redirect_to and is_safe_url(
            url=redirect_to,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure()):
        return redirect_to
    return None


def login_request(request):
    if request.user.is_authenticated:
        return redirect(_get_safe_redirect_url(request) or 'index')

    title = "Login"
    form = UserLoginForm(request.POST or None)
    next_url = _get_safe_redirect_url(request)
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


@require_POST
def logout_request(request):
    logout(request)
    # messages.info(request, "Logged out successfully!")
    return redirect('index')
