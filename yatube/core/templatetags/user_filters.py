from django import template
from django.forms import Field

register = template.Library()


@register.filter
def addclass(field: Field, css: any) -> str:
    """ Модуль фильтра для улучшенной вёрстки HTML-страниц."""
    return field.as_widget(attrs={'class': css})
