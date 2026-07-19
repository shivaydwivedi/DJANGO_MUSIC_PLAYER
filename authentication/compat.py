try:
    from django.utils.http import url_has_allowed_host_and_scheme
except ImportError:  # pragma: no cover - retained for older Django compatibility.
    from django.utils.http import is_safe_url as url_has_allowed_host_and_scheme


def get_safe_redirect_url(request):
    redirect_to = request.POST.get('next') or request.GET.get('next')
    if not redirect_to:
        return None

    try:
        is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    except (TypeError, ValueError):
        return None

    if is_safe:
        return redirect_to
    return None
