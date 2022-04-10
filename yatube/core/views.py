from django.shortcuts import render


def page_not_found(request, exception):
    """Модуль для представления страницы с кодом 404."""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request, exception):
    """Модуль для представления страницы с кодом 403."""
    return render(request, 'core/403.html', status=403)


def server_error(request):
    """ Модуль для представления страницы с кодом 500."""
    return render(request, 'core/500.html', status=500)
