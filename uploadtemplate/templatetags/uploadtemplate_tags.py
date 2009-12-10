import urlparse

from django.conf import settings
from django import template

from uploadtemplate import models

register = template.Library()

@register.simple_tag
def get_static_url(path):
    try:
        theme = models.Theme.objects.get_default()
    except models.Theme.DoesNotExist:
        base = settings.MEDIA_URL
    else:
        base = theme.static_url()

    return urlparse.urljoin(base, path)
