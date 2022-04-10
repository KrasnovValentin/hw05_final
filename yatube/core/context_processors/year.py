from datetime import datetime

from django.http import HttpResponse, HttpRequest


def year(request: HttpRequest) -> HttpResponse:
    """Добавляет переменную с текущим годом."""
    return {'year': datetime.now().year}
