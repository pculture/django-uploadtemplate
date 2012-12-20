import os
import urlparse
import warnings

from django import template
from django.conf import settings
from django.core.files.storage import default_storage

from uploadtemplate.models import Theme

register = template.Library()

class ThemeStaticUrlNode(template.Node):
    def __init__(self, path):
        self.path = path

    def render(self, context):
        if 'uploadtemplate_theme' in context:
            theme = context['uploadtemplate_current_theme']
        else:
            try:
                theme = Theme.objects.get_current()
            except Theme.DoesNotExist:
                theme = None
            context['uploadtemplate_current_theme'] = theme

        path = self.path.resolve(context)
        if path.startswith('/'):
            path = path[1:]

        if theme is not None:
            # Try the new location first.
            name = os.path.join(theme.theme_files_dir, 'static', path)
            if default_storage.exists(name):
                return default_storage.url(name)

            # Backwards-compat: Allow old static paths as well.
            if os.path.exists(os.path.join(theme.static_root(), path)):
                return urlparse.urljoin(theme.static_url(), path)

        if 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
            from django.contrib.staticfiles.storage import staticfiles_storage
            return staticfiles_storage.url(path)

        return urlparse.urljoin(settings.STATIC_URL, path)

@register.tag
def get_static_url(parser, token):
    bits = token.split_contents()
    if len(bits) == 3:
        warnings.warn("{tag_name} no longer takes a `bundled` kwarg".format(tag_name=bits[0]),
                      DeprecationWarning)
    elif len(bits) != 2:
        raise template.TemplateSyntaxError('{tag_name} takes 1 arguments'.format(tag_name=bits[0]))

    return ThemeStaticUrlNode(parser.compile_filter(bits[1]))
