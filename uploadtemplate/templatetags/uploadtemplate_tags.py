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
                theme = Theme.objects.get_default()
            except Theme.DoesNotExist:
                theme = None
            context['uploadtemplate_current_theme'] = theme

        path = self.path.resolve(context)
        if path.startswith('/'):
            path = path[1:]

        if (theme is not None and
            os.path.exists(os.path.join(theme.static_root(), path))):
            base = theme.static_url()
        else:
            if 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
                from django.contrib.staticfiles.storage import staticfiles_storage
                return staticfiles_storage.url(path)

            base = settings.STATIC_URL

        return urlparse.urljoin(base, path)

@register.tag
def get_static_url(parser, token):
    bits = token.split_contents()
    if len(bits) == 3:
        warnings.warn("get_static_url no longer takes a `bundled` kwarg",
                      DeprecationWarning)
    elif len(bits) != 2:
        raise template.TemplateSyntaxError('%s takes 1 arguments' % tokens[0])

    return ThemeStaticUrlNode(parser.compile_filter(bits[1]))
