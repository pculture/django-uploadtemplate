from __future__ import absolute_import

import os
import urlparse
import warnings

from django import template
from django.conf import settings
from django.core.files.storage import default_storage

from uploadtemplate.models import Theme
from uploadtemplate.utils import is_protected_static_file


register = template.Library()


@register.simple_tag(takes_context=True)
def static(context, path):
    try:
        theme = Theme.objects.get_current()
    except Theme.DoesNotExist:
        theme = None

    if path.startswith('/'):
        warnings.warn("static tag paths starting with '/' are deprecated.")
        path = path[1:]

    if theme is not None and not is_protected_static_file(path):
        # Try the new location first.
        name = os.path.join(theme.theme_files_dir, 'static', path)
        if default_storage.exists(name):
            return default_storage.url(name)

        # Backwards-compat: Allow old static paths as well.
        if (hasattr(settings, 'UPLOADTEMPLATE_MEDIA_ROOT') and
            os.path.exists(os.path.join(theme.static_root(), path))):
            warnings.warn("Theme {pk} still uses old static paths.".format(pk=theme.pk))
            return urlparse.urljoin(theme.static_url(), path)

    if 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
        from django.contrib.staticfiles.storage import staticfiles_storage
        return staticfiles_storage.url(path)

    return urlparse.urljoin(settings.STATIC_URL, path)
